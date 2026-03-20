interface LoginResponse {
  user_type: string;
  user_info: any;
  message: string;
  access_token: string;
  token_type: string;
}

class AuthService {
  private static readonly TOKEN_KEY = 'access_token';
  private static readonly USER_KEY = 'user_info';

  static async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data: LoginResponse = await response.json();

    // Save token and user info to localStorage
    localStorage.setItem(this.TOKEN_KEY, data.access_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(data.user_info));

    return data;
  }

  static logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static getUserInfo(): any | null {
    const userInfo = localStorage.getItem(this.USER_KEY);
    return userInfo ? JSON.parse(userInfo) : null;
  }

  static isAuthenticated(): boolean {
    return !!this.getToken();
  }

  static isStudent(): boolean {
    const userInfo = this.getUserInfo();
    return userInfo && 'student_id' in userInfo;
  }

  static isAdmin(): boolean {
    const userInfo = this.getUserInfo();
    return userInfo && userInfo.role === 'administrator';
  }

  static getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? {
      'Authorization': `Bearer ${token}`
    } : {};
  }

  static async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = {
      ...options.headers,
      ...this.getAuthHeaders(),
    };

    return fetch(url, {
      ...options,
      headers,
    });
  }

  static async requestForgotPassword(email: string): Promise<{ message: string }> {
    const response = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Request forgot password failed');
    }

    return data;
  }

  static async validateResetToken(token: string): Promise<boolean> {
    const response = await fetch(`/api/auth/reset-password/validate?token=${encodeURIComponent(token)}`);
    const data = await response.json();
    return Boolean(data.valid);
  }

  static async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, new_password: newPassword }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Reset password failed');
    }

    return data;
  }
}

export default AuthService;