import { useUser } from "@/contexts/UserContext";
import { signOut, deleteUser } from "firebase/auth";
import { auth } from "@/firebase";
import { useNavigate } from "react-router-dom";

export default function Header() {
  const { user, setUser } = useUser();
  const navigate = useNavigate();

  // 로그아웃 버튼 클릭 시 실행
  const handleLogout = async () => {
    if (!user) return;
    const confirmDelete = window.confirm(
      "로그아웃 하시겠습니까?\n\n'예'를 선택하면 계정이 삭제되고 로그아웃됩니다.\n'아니오'를 선택하면 계정은 유지되고 로그아웃만 됩니다."
    );
    if (confirmDelete) {
      // 계정 삭제 + 로그아웃
      try {
        await deleteUser(user);
        setUser(null);
        alert("계정이 삭제되었습니다.");
      } catch (error: any) {
        if (error.code === "auth/requires-recent-login") {
          alert("보안을 위해 다시 로그인 후 계정 삭제가 가능합니다. 로그아웃 후 다시 로그인 해주세요.");
          return;
        } else {
          alert("계정 삭제 실패: " + error.message);
          return;
        }
      }
    }
    // 계정 삭제 여부와 상관없이 로그아웃 진행
    await signOut(auth);
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