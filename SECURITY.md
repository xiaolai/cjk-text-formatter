# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take the security of cjk-text-formatter seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

Please report security vulnerabilities to:
**xiaolaidev@gmail.com**

### What to Include

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: You can expect an initial response within 48 hours
- **Status Update**: We will send you regular updates about our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 7-14 days

### Disclosure Policy

- Please do not publicly disclose the vulnerability until we have had a chance to address it
- We will credit you in the security advisory unless you prefer to remain anonymous
- We will notify you when the vulnerability has been fixed and disclosed

## Security Best Practices

When using cjk-text-formatter:

1. **Input Validation**: While the tool validates file paths, ensure you only process trusted files
2. **File Permissions**: Be mindful of file permissions when using `--inplace` mode
3. **Configuration Files**: Keep configuration files (`.toml`) in trusted locations
4. **Dependencies**: Regularly update dependencies using `pip install --upgrade cjk-text-formatter`

## Known Security Considerations

- **File Path Processing**: The tool processes files provided by users. Always ensure you trust the source of files being processed
- **Regex Processing**: Custom regex rules in configuration files are executed. Only use configuration files from trusted sources
- **HTML Processing**: When processing HTML files with BeautifulSoup, the tool preserves HTML structure. Ensure input HTML is from trusted sources

## Security Updates

Security updates will be released as patch versions (e.g., 0.3.1, 0.3.2) and announced through:

- GitHub Security Advisories
- PyPI release notes
- Project README

## Contact

For general security questions or concerns, please contact:
**xiaolaidev@gmail.com**

Thank you for helping keep cjk-text-formatter secure!
