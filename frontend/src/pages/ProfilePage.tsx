import { Link, useNavigate } from "react-router-dom";
import { Sun, MessageCircle, Home, Settings, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";

const Profile = () => {
  const navigate = useNavigate();
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-72 border-r bg-white hidden lg:block">
        {/* Add left sidebar content here */}
      </div>

      {/* Main Profile Area */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full border-x">
        {/* Header */}
        <header className="py-3 px-4 bg-white border-b flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Heart className="h-5 w-5 text-pink-500 fill-pink-500" />
            <h1 className="text-lg font-medium">My AI Chingu</h1>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 hover:bg-gray-100"
            onClick={() => navigate('/settings')}
          >
            <Settings className="h-5 w-5" />
          </Button>
        </header>

        {/* Profile Content */}
        <div className="flex-1 overflow-auto">
          <div className="py-6 px-4">
            {/* AI Profile Card */}
            <div className="bg-white rounded-2xl p-6 text-center shadow-sm">
              <div className="flex justify-center mb-4">
                <img 
                  src="/example_avatar_profile.png" 
                  alt="AI Friend" 
                  className="w-24 h-24 rounded-full"
                />
              </div>
              <h2 className="text-xl font-medium mb-1">미나</h2>
              <p className="text-gray-500 text-sm mb-4">오늘 날씨가 좋아서 기분이 상쾌해!</p>
              
              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center justify-center mb-1">
                    <span className="text-lg font-medium">5,800</span>
                    <span className="text-sm text-gray-500 ml-1">포인트</span>
                  </div>
                  <p className="text-xs text-gray-500">이제 질문수</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center justify-center mb-1">
                    <span className="text-lg font-medium">23°C</span>
                  </div>
                  <p className="text-xs text-gray-500">현재 위치</p>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 justify-center mb-6">
                <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">#평화로운성격</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">#산책중</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">#운동중</span>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 justify-center">
                <Button className="bg-orange-100 hover:bg-orange-200 text-orange-600 rounded-full px-6">
                  선물하기
                </Button>
                <Button className="bg-blue-100 hover:bg-blue-200 text-blue-600 rounded-full px-6">
                  놀아주기
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <nav className="py-2 grid grid-cols-3 border-t bg-white">
          <Link to="/signup" className="flex flex-col items-center justify-center">
            <Home className="h-6 w-6 text-gray-400" />
            <span className="text-[11px] text-gray-400 mt-1">홈</span>
          </Link>
          <Link to="/chat" className="flex flex-col items-center justify-center">
            <MessageCircle className="h-6 w-6 text-gray-400" />
            <span className="text-[11px] text-gray-400 mt-1">채팅</span>
          </Link>
          <Link to="/profile" className="flex flex-col items-center justify-center">
            <Sun className="h-6 w-6 text-blue-500" />
            <span className="text-[11px] text-blue-500 mt-1">프로필</span>
          </Link>
        </nav>
      </div>

      {/* Right Sidebar */}
      <div className="w-72 border-l bg-white hidden lg:block">
        {/* Add right sidebar content here */}
      </div>
    </div>
  );
};

export default Profile;
