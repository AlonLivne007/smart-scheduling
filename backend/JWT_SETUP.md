# JWT Authentication Setup

This document explains the JWT authentication implementation in the Smart Scheduling API.

## 🔧 Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/scheduler_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3

# Application Configuration
DEBUG=True
```

## 📦 Dependencies

The following dependencies are required and already added to `requirements.txt`:

```
python-jose[cryptography]
```

## 🚀 API Endpoints

### Authentication Endpoints

#### 1. User Login

```http
POST /users/login
Content-Type: application/json

{
  "user_email": "user@example.com",
  "user_password": "password123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "user_full_name": "John Doe",
    "user_email": "user@example.com",
    "is_manager": false,
    "roles": []
  }
}
```

## 🔐 Security Features

### JWT Token Structure

- **Algorithm**: HS256
- **Expiration**: 3 days (configurable)
- **Payload**: Contains user email and user_id
- **Secret Key**: Configurable via environment variable

### Token Validation

- Automatic expiration checking
- Signature verification
- Proper error handling for invalid tokens

## 🛠️ Usage Examples

### Frontend Integration

#### Frontend Integration Example

```javascript
const loginUser = async (email, password) => {
  const response = await fetch("/users/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_email: email,
      user_password: password,
    }),
  });

  const data = await response.json();

  if (response.ok) {
    // Store token for future requests
    localStorage.setItem("access_token", data.access_token);
    // User data is already available in data.user
    console.log("User logged in:", data.user);
    return data;
  } else {
    throw new Error(data.detail);
  }
};
```

## 🔧 Configuration Options

### Environment Variables

| Variable          | Default                                               | Description                |
| ----------------- | ----------------------------------------------------- | -------------------------- |
| `JWT_SECRET_KEY`  | `your-super-secret-jwt-key-change-this-in-production` | Secret key for JWT signing |
| `JWT_ALGORITHM`   | `HS256`                                               | JWT signing algorithm      |
| `JWT_EXPIRE_DAYS` | `3`                                                   | Token expiration in days   |

### Security Recommendations

1. **Change the default JWT secret key** in production
2. **Use environment variables** for all sensitive configuration
3. **Implement token refresh** for long-lived sessions
4. **Add rate limiting** for login attempts
5. **Use HTTPS** in production

## 🚨 Error Handling

### Common Error Responses

#### Invalid Credentials

```json
{
  "detail": "Invalid email or password"
}
```

#### Invalid Token

```json
{
  "detail": "Invalid or expired token"
}
```

#### Missing Authorization Header

```json
{
  "detail": "Invalid authorization header format"
}
```

## 📝 Development Notes

- JWT tokens are stateless and don't require server-side storage
- Token expiration is handled automatically
- All protected routes require the `Authorization: Bearer <token>` header
- The `verify_token()` function can be reused across different protected endpoints
