
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

<<<<<<< HEAD
=======
import { auth, googleProvider } from "@/firebase";
import { signInWithPopup } from "firebase/auth";
import { useUser } from "@/contexts/UserContext";
import { deleteUser } from "firebase/auth";

>>>>>>> origin/taesu-feature
const SignUp = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const navigate = useNavigate();

<<<<<<< HEAD
=======
  const { user, setUser } = useUser();
  // 구글 로그인 함수
  const handleGoogleLogin = async () => {
    if (user) {
      alert("이미 로그인되어 있습니다.");
      return;
    }
    try {
      const result = await signInWithPopup(auth, googleProvider);
      setUser(result.user);
      navigate('/create-ai-friend');
    } catch (error) {
      alert("구글 로그인 실패: " + error);
    }
  };

  // 계정 삭제 함수
  const handleDeleteAccount = async () => {
    if (!user) {
      alert("로그인 후 이용 가능합니다.");
      return;
    }
    if (!window.confirm("정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")) {
      return;
    }
    try {
      await deleteUser(user);
      setUser(null);
      alert("계정이 삭제되었습니다.");
      navigate("/");
    } catch (error: any) {
      // 재로그인 필요 에러 처리
      if (error.code === "auth/requires-recent-login") {
        alert("보안을 위해 다시 로그인 후 계정 삭제가 가능합니다. 로그아웃 후 다시 로그인 해주세요.");
      } else {
        alert("계정 삭제 실패: " + error.message);
      }
    }
  };
  
>>>>>>> origin/taesu-feature
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login attempted with:", { email, password, rememberMe });
    // Redirect to create AI friend page after login
    navigate('/create-ai-friend');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Background with images */}
      <div className="hidden md:flex md:w-1/2 bg-sky-100 items-center justify-center p-8">
        <div className="max-w-md text-center space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg overflow-hidden">
              <img 
                src="/example.jpg" 
                alt="AI Friend" 
                className="w-full h-auto"
              />
            </div>
            <div className="rounded-lg overflow-hidden">
              <img 
                src="/example_avatar.png" 
                alt="Child with AI Friend" 
                className="w-full h-auto"
              />
            </div>
          </div>
          <h2 className="text-xl font-medium text-gray-700">나의 어린시절 오랜친구</h2>
          <p className="text-gray-600">
            성장기에 누구나 가졌던 상상 속 친구<br />
            이제 AI로 만나보세요
          </p>
          <p className="text-sky-500 text-sm">
            © AIC 2025
          </p>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-4 md:p-8">
        <div className="w-full max-w-md space-y-6">
          <div className="flex items-center justify-center mb-4">
            <img src="/logo.svg" alt="My AI Chingu" className="h-8 w-8" />
            <span className="ml-2 text-lg font-medium">My AI Chingu</span>
          </div>

          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold">환영합니다</h1>
            <p className="text-gray-600">계정에 로그인하고 AI 친구를 만나보세요</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label className="text-gray-500 mb-1 block">이메일</Label>
                <div className="relative">
                  <span className="absolute left-3 top-3 text-gray-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                  </span>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="이메일 주소를 입력하세요"
                    className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                    required
                  />
                </div>
              </div>
              
              <div>
                <Label className="text-gray-500 mb-1 block">비밀번호</Label>
                <div className="relative">
                  <span className="absolute left-3 top-3 text-gray-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"/><circle cx="16.5" cy="7.5" r=".5"/></svg>
                  </span>
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="비밀번호를 입력하세요"
                    className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked === true)}
                className="border-2 border-gray-300"
              />
              <Label htmlFor="remember" className="ml-2 text-sm text-gray-600">자동 로그인</Label>
              <a href="#" className="ml-auto text-sm text-blue-400 hover:underline">비밀번호찾기</a>
            </div>

            <Button type="submit" className="w-full py-3 bg-blue-400 hover:bg-blue-500 text-white rounded-lg font-medium">
              로그인
            </Button>

            <div className="text-center text-gray-500 text-sm">
              <span>간편 로그인</span>
              <div className="mt-4 flex justify-center space-x-4">
<<<<<<< HEAD
                <button className="w-12 h-12 flex items-center justify-center rounded-lg border border-gray-300 hover:border-gray-400 p-2">
=======
                <button className="w-12 h-12 flex items-center justify-center rounded-lg border border-gray-300 hover:border-gray-400 p-2" onClick={handleGoogleLogin}>
>>>>>>> origin/taesu-feature
                  <img src="/Google__G__logo.svg.png" alt="Google" className="w-full h-full object-contain" />
                </button>
                <button className="w-12 h-12 flex items-center justify-center rounded-lg border border-gray-300 hover:border-gray-400 p-2">
                  <img src="/NAVER_LOGO.png" alt="Naver" className="w-full h-full object-contain" />
                </button>
                <button className="w-12 h-12 flex items-center justify-center rounded-lg border border-gray-300 hover:border-gray-400 p-2">
                  <img src="/instagram_logo.jpg" alt="Instagram" className="w-full h-full object-contain" />
                </button>
              </div>
            </div>

            <div className="text-center">
              <span className="text-gray-600 text-sm">아직 계정이 없으신가요? </span>
              <a href="#" className="text-blue-400 hover:underline text-sm">회원가입</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SignUp;
