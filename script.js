// Auth utility functions
class Auth {
    static isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }

    static getToken() {
        return localStorage.getItem('access_token');
    }

    static logout() {
        localStorage.removeItem('access_token');
        window.location.href = 'index.html';
    }

    static async checkAuth() {
        const token = this.getToken();
        if (!token) {
            window.location.href = 'login.html';
            return false;
        }

        try {
            const response = await fetch('/api/v1/auth/verify', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                this.logout();
                return false;
            }

            return true;
        } catch (error) {
            console.error('Auth verification failed:', error);
            this.logout();
            return false;
        }
    }
}

// Update navigation based on auth state
async function updateNavbar() {
    const token = localStorage.getItem('access_token');
    const authLinks = document.querySelectorAll('.auth-links');
    const userLinks = document.querySelectorAll('.user-links');

    // Clear inline styles first to ensure classes take effect
    authLinks.forEach(link => link.style.display = '');
    userLinks.forEach(link => link.style.display = '');

    if (token) {
        authLinks.forEach(link => link.classList.add('auth-hidden'));
        userLinks.forEach(link => link.classList.remove('auth-hidden'));

        try {
            // Fetch user profile
            const userResponse = await fetch('/api/v1/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (userResponse.ok) {
                const userData = await userResponse.json();

                // Update Name: First Name + Last Initial
                const nameEl = document.getElementById('header-user-name');
                if (nameEl) {
                    const first = userData.first_name || 'User';
                    const last = userData.last_name || '';
                    const lastInitial = last ? ` ${last.charAt(0)}.` : '';
                    nameEl.textContent = `${first}${lastInitial}`;
                }

                // Update Avatar
                const avatarEl = document.getElementById('header-user-avatar');
                if (avatarEl) {
                    avatarEl.src = userData.picture || `https://ui-avatars.com/api/?name=${userData.first_name}+${userData.last_name}&background=random`;
                }

                // Update Balance from User Data (if available) or fetch wallet
                // Requirement 7: Display balance from users.balance
                let balance = userData.balance;

                // Fallback or double check with wallet endpoint if needed? 
                // Requirement says "Display balance from users.balance" so we trust userData.balance for header.
                // However, we still might need wallet endpoint for the Wallet page specific logic if separate.

                const formattedBalance = formatCurrency(balance);

                // Update header balance (index/item pages)
                const headerBalEl = document.getElementById('header-user-balance');
                if (headerBalEl) headerBalEl.textContent = formattedBalance;

                // Sync Wallet Page Balance if on wallet page
                const walletNavBal = document.getElementById('wallet-balance-nav');
                if (walletNavBal) walletNavBal.textContent = formattedBalance;

            } else if (userResponse.status === 401) {
                // Token expired or invalid
                Auth.logout();
                return;
            }
            // Removed separate wallet fetch for header as per requirement to use user profile data

        } catch (error) {
            console.error('Error updating navbar:', error);
        }

    } else {
        authLinks.forEach(link => link.classList.remove('auth-hidden'));
        userLinks.forEach(link => link.classList.add('auth-hidden'));
    }
}

// Initialize auth checks on page load
document.addEventListener('DOMContentLoaded', function () {
    // Check auth for protected pages
    if (window.location.pathname.endsWith('wallet.html')) {
        Auth.checkAuth();
    }

    // Update navbar based on auth status
    updateNavbar();

    // Attach logout handlers
    document.querySelectorAll('.logout-btn').forEach(btn => {
        btn.addEventListener('click', Auth.logout);
    });
});

// Shared API helper function
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers.Authorization = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, options);
        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.message || 'Request failed');
        }

        return responseData;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Format currency helper
function formatCurrency(amount) {
    return '₦' + amount.toLocaleString();
}

// Initialize feather icons
document.addEventListener('DOMContentLoaded', function () {
    if (window.feather) {
        feather.replace();
    }
});