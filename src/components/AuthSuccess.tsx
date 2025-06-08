import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../services/api';

const AuthSuccess = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const verifySession = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/user`, {
          credentials: 'include',
        });

        if (response.ok) {
          const user = await response.json();
          console.log('✅ User session found:', user);
          // Optionally store in state/context
          navigate('/dashboard'); // or your landing route
        } else {
          console.warn('❌ No session found, redirecting to login');
          navigate('/login');
        }
      } catch (err) {
        console.error('⚠️ Error verifying session:', err);
        navigate('/login');
      }
    };

    verifySession();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center text-xl font-semibold text-gray-700">
      Logging you in securely...
    </div>
  );
};

export default AuthSuccess;
