#!/usr/bin/env bash

# Get the script directory
if [[ -L ${BASH_SOURCE[0]} ]]; then
    script_dir=$(dirname $(readlink ${BASH_SOURCE[0]}))
else
    script_dir=$(cd $(dirname ${BASH_SOURCE[0]}); pwd -P)
fi
source "${script_dir}/message.sh"

# File lock for preventing concurrent installations
LOCK_FILE="${script_dir}/.install.lock"

# Cleanup function for rollback on failure/interruption
cleanup() {
    # Delete lock file
    rm -f "${LOCK_FILE}"

    # Delete installed files (only if they were created during installation)
    if [ -n "${bin_path}" ] && [ -f "${bin_path}" ]; then
        $cmd_prefix rm -f "${bin_path}"
    fi
    if [ -n "${conf_path}" ] && [ -f "${conf_path}" ]; then
        $cmd_prefix rm -f "${conf_path}"
    fi
    if [ -n "${service_path}" ] && [ -f "${service_path}" ]; then
        $cmd_prefix rm -f "${service_path}"
    fi
    # Delete backup file created by sed -i.bak
    if [ -n "${service_path}" ] && [ -f "${service_path}.bak" ]; then
        $cmd_prefix rm -f "${service_path}.bak"
    fi

    exit 1
}

# Set trap for interruption signals and errors
trap cleanup SIGINT SIGTERM ERR

# Enable exit on error
set -e

# run as root user
if [ $UID != 0 ]; then
    if ! sudo -v; then
        ERR "需要 sudo 权限才能运行此脚本"
        exit 1
    fi
    cmd_prefix="sudo "
fi
INFO "Git-Webhooks-Server Installation."

# for uninstall
if [[ $1 = '--uninstall' ]];then
	# Disable trap for uninstall to avoid rollback
	trap - SIGINT SIGTERM ERR
	# Disable set -e for uninstall to handle errors gracefully
	set +e
	if [ -f "${script_dir}/installed.env" ]; then
		source "${script_dir}/installed.env"
		QUES_N "Confirm to uninstall? (N/y)" confirm
		if [[ "${confirm:0:1}" == [Yy] ]]; then
			# Stop and disable service (may fail if not installed)
			if command -v systemctl > /dev/null; then
				$cmd_prefix systemctl stop git-webhooks-server 2>/dev/null || true
				$cmd_prefix systemctl disable git-webhooks-server 2>/dev/null || true
			fi
			if [ -f "$bin_path" ];then
				INFO_N "Uninstall: ${bin_path}"
				$cmd_prefix rm -f "$bin_path"
				if [ -f "$bin_path" ];then WARN " [Fail]"; else INFO " [OK]"; fi
			fi
			if [ -f "$conf_path" ];then
				INFO_N "Uninstall: ${conf_path}"
				$cmd_prefix rm -f "$conf_path"
				if [ -f "$conf_path" ];then WARN " [Fail]"; else INFO " [OK]"; fi
			fi
			if [ -f "$service_path" ];then
				INFO_N "Uninstall: ${service_path}"
				$cmd_prefix rm -f "$service_path"
				if [ -f "$service_path" ];then WARN " [Fail]"; else INFO " [OK]"; fi
			fi
			$cmd_prefix rm -f "${script_dir}/installed.env"
		fi
	else
		ERR "You have not installed"
	fi
	exit 0
fi

if [ -f "${script_dir}/installed.env" ]; then
	WARN "You have already installed this service, you can run the \"./install.sh --uninstall\" to uninstall it."
	exit 1
fi

# Check lock file to prevent concurrent installations
if [ -f "${LOCK_FILE}" ]; then
	ERR "已有安装实例正在运行"
	exit 1
fi

# Create lock file
touch "${LOCK_FILE}"

# enter install directory
QUES_N "Enter install directory (default: /usr/local/bin)" bin_path
[ -z "$bin_path" ] && bin_path='/usr/local/bin'
[ ! -d "$bin_path" ] && ERR "No such directory: ${bin_path}" && exit 1
bin_path="${bin_path}/git-webhooks-server.py"

# enter configuration directory
QUES_N "Enter configuration directory (default: /usr/local/etc)" conf_path
[ -z "$conf_path" ] && conf_path='/usr/local/etc'
[ ! -d "$conf_path" ] && ERR "No such directory: ${conf_path}" && exit 1
conf_path="${conf_path}/git-webhooks-server.ini"

# copy bin file
INFO_N "Installing: ${script_dir}/git-webhooks-server.py => ${bin_path}"
# clean
[ -f "$bin_path" ] && $cmd_prefix rm -f "$bin_path"
# copy file and set as executable
$cmd_prefix cp -f "${script_dir}/git-webhooks-server.py" "$bin_path"
$cmd_prefix chmod +x "$bin_path"
if [ -f "$bin_path" ];then
	INFO " [OK]"
	echo "bin_path=${bin_path}" >> "${script_dir}/installed.env"
else
	ERR " [Fail]"
	exit 1
fi

INFO_N "Installing: ${script_dir}/git-webhooks-server.ini.sample => ${conf_path}"
# clean
[ -f "$conf_path" ] && $cmd_prefix rm -f "$conf_path"
# copy file
$cmd_prefix cp "${script_dir}/git-webhooks-server.ini.sample" "$conf_path"
if [ -f "$conf_path" ];then
	INFO " [OK]"
	echo "conf_path=${conf_path}" >> "${script_dir}/installed.env"
else
	ERR " [Fail]"
	exit 1
fi

#
if command -v systemctl > /dev/null; then
	QUES_N "Install as systemd service? (Y/n)" confirm
	if [[ "${confirm:0:1}" == [Yy] ]]; then
		service_dir="/usr/lib/systemd/system"
		service_path="${service_dir}/git-webhooks-server.service"
		INFO_N "Installing: ${script_dir}/git-webhooks-server.service.sample => ${service_path}"
		# clean
		[ -f "$service_path" ] && $cmd_prefix rm -f "$service_path"
		# copy file
		[ ! -d "$service_dir" ] && $cmd_prefix mkdir -p "$service_dir"
		$cmd_prefix cp -f "${script_dir}/git-webhooks-server.service.sample" "$service_path"
		# replace the service start command
		$cmd_prefix sed -i.bak "s/REPLACE_BY_INSTALL/${bin_path//\//\\\/} -c ${conf_path//\//\\\/}/g" "$service_path"
		$cmd_prefix rm -f "${service_path}.bak"
		if [ -f "$service_path" ];then
			INFO " [OK]"
			echo "service_path=${service_path}" >> "${script_dir}/installed.env"
		else
			ERR " [Fail]"
			exit 1
		fi
		# startup
		QUES_N "Enable and startup the service? (Y/n)" confirm
		if [[ "${confirm:0:1}" == [Yy] ]]; then
			if ! $cmd_prefix systemctl enable git-webhooks-server 2>/dev/null; then
				WARN "systemctl enable 失败"
				QUES_N "是否继续安装？ (Y/n)" confirm
				if [[ "${confirm:0:1}" =~ [Nn] ]]; then
					exit 1
				fi
			fi
			if ! $cmd_prefix systemctl start git-webhooks-server 2>/dev/null; then
				WARN "systemctl start 失败"
				QUES_N "是否继续安装？ (Y/n)" confirm
				if [[ "${confirm:0:1}" =~ [Nn] ]]; then
					exit 1
				fi
			fi
		fi
	fi
fi

# Installation successful - delete lock file and disable trap
rm -f "${LOCK_FILE}"
trap - SIGINT SIGTERM ERR
INFO "Installation completed successfully!"
