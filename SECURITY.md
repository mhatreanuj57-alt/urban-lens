# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a vulnerability

Please report security vulnerabilities by opening a **private** issue or contacting the maintainers directly. Do not disclose sensitive issues publicly.

## Security measures

- All passwords are hashed with bcrypt
- JWT tokens expire after 7 days
- Media uploads are validated for type and size
- EXIF data is stripped from public derivatives
- Faces and number plates are blurred in public media
- Database queries use parameterized statements (SQLAlchemy)
- CORS is configured for known origins only
