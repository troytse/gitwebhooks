"""HTTP 和响应常量定义

定义项目中使用的所有常量。
"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_NOT_ACCEPTABLE = 406
HTTP_PRECONDITION_FAILED = 412
HTTP_INTERNAL_SERVER_ERROR = 500

# HTTP Content Types
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_FORM_URLENCODED = 'application/x-www-form-urlencoded'

# HTTP Headers
HEADER_CONTENT_TYPE = 'Content-Type'
HEADER_CONTENT_LENGTH = 'Content-Length'
HEADER_GITHUB_EVENT = 'X-GitHub-Event'
HEADER_GITHUB_SIGNATURE = 'X-Hub-Signature'
HEADER_GITEE_EVENT = 'X-Gitee-Event'
HEADER_GITEE_TOKEN = 'X-Gitee-Token'
HEADER_GITEE_TIMESTAMP = 'X-Gitee-Timestamp'
HEADER_GITLAB_EVENT = 'X-Gitlab-Event'
HEADER_GITLAB_TOKEN = 'X-Gitlab-Token'

# Response Messages
MESSAGE_OK = b'OK'
MESSAGE_FORBIDDEN = 'Forbidden'
MESSAGE_BAD_REQUEST = 'Bad Request'
MESSAGE_UNAUTHORIZED = 'Unauthorized'
MESSAGE_NOT_FOUND = 'Not Found'
MESSAGE_NOT_ACCEPTABLE = 'Not Acceptable'
MESSAGE_PRECONDITION_FAILED = 'Precondition Failed'
MESSAGE_INTERNAL_SERVER_ERROR = 'Internal Server Error'

# Reserved configuration sections
RESERVED_SECTIONS = {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}
