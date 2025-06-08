import { useUser } from "@/contexts/UserContext";
import { useNavigate, Link, useLocation } from "react-router-dom";

export default function Header() {
  const { user, setUser } = useUser();
  const navigate = useNavigate();
  const location = useLocation();

  // 로그아웃 버튼 클릭 시 실행
  const handleLogout = async () => {
    if (!user) return;
    
    console.log("Firebase authentication disabled for testing. Logging out mock user.");
    setUser(null);
    navigate("/signup");
  };

  return (
    <header className="w-full bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* 빈 자리 영역 */}
          <div className="flex">
          </div>

          {/* User Profile */}
          {user ? (
            <div className="flex items-center space-x-3">
              <img
                src={user.photoURL || "/default_profile.png"}
                alt="profile"
                className="w-8 h-8 rounded-full border"
              />
              <span className="text-sm font-medium text-gray-700">{user.displayName || user.email}</span>
              <button
                onClick={handleLogout}
                className="ml-2 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                로그아웃
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-3">
              <Link 
                to="/signup"
                className="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
              >
                로그인
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}