import { useUser } from "@/contexts/UserContext";
import { useNavigate } from "react-router-dom";

export default function Header() {
  const { user, setUser } = useUser();
  const navigate = useNavigate();

  // 로그아웃 버튼 클릭 시 실행
  const handleLogout = async () => {
    if (!user) return;
    
    console.log("Firebase authentication disabled for testing. Logging out mock user.");
    setUser(null);
    navigate("/signup");
  };

  return (
    <header className="w-full flex justify-end items-center p-4 bg-white shadow">
      {user ? (
        <div className="flex items-center space-x-2">
          <img
            src={user.photoURL || "/default_profile.png"}
            alt="profile"
            className="w-8 h-8 rounded-full border"
          />
          <span className="text-sm">{user.displayName || user.email}</span>
          <button
            onClick={handleLogout}
            className="ml-2 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
          >
            로그아웃
          </button>
        </div>
      ) : null}
    </header>
  );
}