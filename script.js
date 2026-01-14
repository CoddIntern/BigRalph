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
            const response = await fetch('/api/v1/auth/me', {
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

    // Clear inline styles first
    authLinks.forEach(link => link.style.display = '');
    userLinks.forEach(link => link.style.display = '');

    if (token) {
        authLinks.forEach(link => link.classList.add('auth-hidden'));
        userLinks.forEach(link => link.classList.remove('auth-hidden'));

        try {
            const userResponse = await fetch('/api/v1/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (userResponse.ok) {
                const userData = await userResponse.json();

                // Update Name
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

                // Update Balance
                const balance = userData.balance;
                const formattedBalance = formatCurrency(balance);

                const headerBalEl = document.getElementById('header-user-balance');
                if (headerBalEl) headerBalEl.textContent = formattedBalance;

                const walletNavBal = document.getElementById('wallet-balance-nav');
                if (walletNavBal) walletNavBal.textContent = formattedBalance;

            } else if (userResponse.status === 401) {
                Auth.logout();
                return;
            }
        } catch (error) {
            console.error('Error updating navbar:', error);
        }

    } else {
        authLinks.forEach(link => link.classList.remove('auth-hidden'));
        userLinks.forEach(link => link.classList.add('auth-hidden'));
    }
}

// Dropdown toggle functionality
function setupDropdown() {
    const dropdownBtn = document.querySelector('.dropdown > button');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    if (!dropdownBtn || !dropdownMenu) return;

    // Use a clearer state management
    dropdownBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.remove('show');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    if (window.location.pathname.endsWith('wallet.html')) {
        Auth.checkAuth();
    }

    updateNavbar();
    setupDropdown();

    document.querySelectorAll('.logout-btn').forEach(btn => {
        btn.addEventListener('click', Auth.logout);
    });

    if (window.feather) {
        feather.replace();
    }
});

// Shared API helper function
async function apiRequest(url, method = 'GET', data = null) {
    const API_BASE = '/api/v1';
    const fullUrl = url.startsWith('/') ? url : `${API_BASE}/${url}`;

    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) options.body = JSON.stringify(data);

    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers.Authorization = `Bearer ${token}`;
    }

    try {
        const response = await fetch(fullUrl, options);

        // Handle token expiration
        if (response.status === 401) {
            Auth.logout();
            throw new Error('Session expired. Please log in again.');
        }

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || responseData.message || 'Request failed');
        }

        return responseData;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}


// Format currency helper
function formatCurrency(amount) {
    return '₦' + (amount || 0).toLocaleString();
}