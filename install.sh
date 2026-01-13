#!/usr/bin/env bash

# Get the script directory
if [[ -L ${BASH_SOURCE[0]} ]]; then
    script_dir=$(dirname $(readlink ${BASH_SOURCE[0]}))
else
    script_dir=$(cd $(dirname ${BASH_SOURCE[0]}); pwd -P)
fi
source "${script_dir}/message.sh"

# Verbose mode flag
VERBOSE_MODE=false
# Uninstall mode flag
UNINSTALL_MODE=false

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE_MODE=true
            shift
            ;;
        --uninstall)
            UNINSTALL_MODE=true
            shift
            ;;
    esac
done

# Enable verbose mode if requested
if [ "$VERBOSE_MODE" = true ]; then
    set -x
    exec 2>&1
fi

# File lock for preventing concurrent installations
LOCK_FILE="${script_dir}/.install.lock"

# Clean up stale lock file (more than 1 hour old)
if [ -f "${LOCK_FILE}" ]; then
    if find "${LOCK_FILE}" -maxdepth 0 -mmin +60 2>/dev/null; then
        WARN "发现陈旧的锁文件，正在清理..."
        rm -f "${LOCK_FILE}"
    fi
fi

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
    # Clean up temporary service files (use specific pattern to avoid race)
    rm -f "${script_dir}/.tmp_service.$$"
    rm -f "${script_dir}/.tmp_service.$$".*

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
INFO "Git-Webhooks-Server Installation (v2.0 - Modular)"

# for uninstall
if [ "$UNINSTALL_MODE" = true ]; then
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
			if [ -n "${bin_path}" ] && [ -f "$bin_path" ];then
				INFO_N "Uninstall: ${bin_path}"
				$cmd_prefix rm -f "$bin_path"
				if [ -f "$bin_path" ];then WARN " [Fail]"; else INFO " [OK]"; fi
			fi
			if [ -n "${conf_path}" ] && [ -f "$conf_path" ];then
				INFO_N "Uninstall: ${conf_path}"
				$cmd_prefix rm -f "$conf_path"
				if [ -f "$conf_path" ];then WARN " [Fail]"; else INFO " [OK]"; fi
			fi
			if [ -n "${service_path}" ] && [ -f "$service_path" ];then
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

# Verify gitwebhooks package exists in source directory
if [ ! -d "${script_dir}/gitwebhooks" ]; then
    ERR "gitwebhooks package not found in source directory: ${script_dir}"
    ERR "Please run this script from the project root directory."
    exit 1
fi

# enter install directory
QUES_N "Enter binary install directory (default: /usr/local/bin)" bin_dir
[ -z "$bin_dir" ] && bin_dir='/usr/local/bin'
[ ! -d "$bin_dir" ] && ERR "No such directory: ${bin_dir}" && exit 1
bin_path="${bin_dir}/gitwebhooks-cli"

# enter configuration directory
QUES_N "Enter configuration directory (default: /usr/local/etc)" conf_dir
[ -z "$conf_dir" ] && conf_dir='/usr/local/etc'
[ ! -d "$conf_dir" ] && ERR "No such directory: ${conf_dir}" && exit 1
conf_path="${conf_dir}/git-webhooks-server.ini"

# Store source directory for reference
SOURCE_DIR="$(cd "${script_dir}" && pwd)"

# Install CLI wrapper using hard link
INFO_N "Installing: ${script_dir}/gitwebhooks-cli => ${bin_path} (hard link)"
# clean
[ -f "$bin_path" ] && $cmd_prefix rm -f "$bin_path"
# Create hard link to the CLI wrapper
$cmd_prefix ln "${script_dir}/gitwebhooks-cli" "$bin_path" || {
    # Hard link failed (possibly different filesystem), fall back to copy
    WARN " Hard link failed, using copy instead"
    $cmd_prefix cp -f "${script_dir}/gitwebhooks-cli" "$bin_path"
}
$cmd_prefix chmod +x "$bin_path"
if [ -f "$bin_path" ];then
	INFO " [OK]"
	echo "bin_path=${bin_path}" >> "${script_dir}/installed.env"
	echo "source_dir=${SOURCE_DIR}" >> "${script_dir}/installed.env"
else
	ERR " [Fail]"
	exit 1
fi

# Install configuration file
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

# Install systemd service
if command -v systemctl > /dev/null; then
	QUES_N "Install as systemd service? (Y/n)" confirm
	if [[ "${confirm:0:1}" == [Yy] ]]; then
		service_dir="/usr/lib/systemd/system"
		service_path="${service_dir}/git-webhooks-server.service"
		INFO_N "Installing: ${script_dir}/git-webhooks-server.service.sample => ${service_path}"
		# Ensure service directory exists
		if [ ! -d "$service_dir" ]; then
			$cmd_prefix mkdir -p "$service_dir" || {
				ERR " [Fail] Cannot create directory: ${service_dir}"
				exit 1
			}
		fi
		# Remove existing file if present (force remove even if read-only)
		if [ -f "$service_path" ]; then
			$cmd_prefix rm -f "$service_path" || {
				ERR " [Fail] Cannot remove existing file: ${service_path}"
				exit 1
			}
		fi
		# Copy service file template to temp location first
		tmp_service_file="${script_dir}/.tmp_service.$$"
		cp "${script_dir}/git-webhooks-server.service.sample" "$tmp_service_file" || {
			ERR " [Fail] Cannot copy service template"
			exit 1
		}
		# Replace the service start command in temp file
		escaped_bin_path="${bin_path//\//\\/}"
		escaped_conf_path="${conf_path//\//\\/}"
		sed "s|REPLACE_BY_INSTALL|${escaped_bin_path} -c ${escaped_conf_path}|g" "$tmp_service_file" > "$tmp_service_file.new" || {
			ERR " [Fail] Cannot update service file with paths"
			rm -f "$tmp_service_file" "$tmp_service_file.new"
			exit 1
		}
		mv "$tmp_service_file.new" "$tmp_service_file"
		# Install the service file
		$cmd_prefix cp "$tmp_service_file" "$service_path" || {
			ERR " [Fail] Cannot copy service file to ${service_path}"
			rm -f "$tmp_service_file"
			exit 1
		}
		rm -f "$tmp_service_file"
		# Verify the service file was created correctly
		if [ ! -f "$service_path" ]; then
			ERR " [Fail] Service file not found after installation"
			exit 1
		fi
		# Verify the service file contains the correct paths
		if ! grep -q "$bin_path" "$service_path"; then
			ERR " [Fail] Service file does not contain correct binary path"
			$cmd_prefix cat "$service_path" >&2
			exit 1
		fi
		INFO " [OK]"
		echo "service_path=${service_path}" >> "${script_dir}/installed.env"
		# startup
		QUES_N "Enable and startup the service? (Y/n)" confirm
		if [[ "${confirm:0:1}" == [Yy] ]]; then
			if ! $cmd_prefix systemctl daemon-reload 2>/dev/null; then
				WARN "systemctl daemon-reload 失败"
			fi
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
INFO ""
INFO "安装位置:"
INFO "  CLI 入口点: ${bin_path} (硬链接到源文件)"
INFO "  源码目录:   ${SOURCE_DIR}"
INFO "  配置文件:   ${conf_path}"
INFO ""
INFO "重要提示:"
INFO "  请保持源码目录 (${SOURCE_DIR}) 完整，CLI 需要从该目录加载 gitwebhooks 包"
INFO ""
INFO "Usage:"
INFO "  Direct: ${bin_path} -c ${conf_path}"
INFO "  Service: systemctl start git-webhooks-server"
