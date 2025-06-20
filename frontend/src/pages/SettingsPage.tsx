import { useState } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Link, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  Settings,
  Bell,
  Database,
  Info,
  Edit,
  Volume2,
  MapPin,
  Shield,
  FileText,
  HelpCircle,
  Footprints,
} from "lucide-react";

const SettingsPage = () => {
  const navigate = useNavigate();
  const [pushNotifications, setPushNotifications] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="py-4 px-4 bg-white border-b flex items-center">
        <button
          onClick={() => navigate(-1)}
          className="p-1 rounded-lg hover:bg-gray-100"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-lg font-medium flex-1 text-center pr-6">설정</h1>
      </header>

      <div className="max-w-md mx-auto p-4 space-y-8">
        {/* User Profile Section */}
        <div className="bg-white rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage
                src="/lovable-uploads/468b3bb5-ece7-4600-8db8-f401827a591a.png"
                alt="김유진"
              />
              <AvatarFallback>김</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="font-medium">김유진</h2>
              <p className="text-sm text-gray-500">yujin.kim@email.com</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="rounded-full bg-orange-100 text-orange-600 border-orange-200 hover:bg-orange-200"
          >
            프로필
          </Button>
        </div>

        {/* AI Friend Settings Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-2">
            <Settings className="h-5 w-5 text-sky-500" />
            <h3 className="font-medium text-gray-800">AI 친구 설정</h3>
          </div>

          <div className="bg-white rounded-lg divide-y">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Edit className="h-5 w-5 text-orange-500" />
                <span>아바타 외형 변경</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-sky-500">변경</span>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </div>
            </div>

            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Volume2 className="h-5 w-5 text-orange-500" />
                <span>목소리 톤/스타일 설정</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-sky-500">설정</span>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Notification Settings Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-2">
            <Bell className="h-5 w-5 text-orange-500" />
            <h3 className="font-medium text-gray-800">알림 설정</h3>
          </div>

          <div className="bg-white rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5 text-sky-500" />
                <span>푸시 알림</span>
              </div>
              <Switch
                checked={pushNotifications}
                onCheckedChange={setPushNotifications}
              />
            </div>
          </div>
        </div>

        {/* Data Management Settings Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-2">
            <Database className="h-5 w-5 text-sky-500" />
            <h3 className="font-medium text-gray-800">데이터 연동 설정</h3>
          </div>

          <div className="bg-white rounded-lg divide-y">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Footprints className="h-5 w-5 text-orange-500" />
                <span>걸음 수 데이터 연동</span>
              </div>
              <Switch defaultChecked={false} />
            </div>

            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-orange-500" />
                <span>위치 정보 접근 권한</span>
              </div>
              <Switch defaultChecked={false} />
            </div>
          </div>
        </div>

        {/* App Information Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-2">
            <Info className="h-5 w-5 text-orange-500" />
            <h3 className="font-medium text-gray-800">앱 정보</h3>
          </div>

          <div className="bg-white rounded-lg divide-y">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-orange-500" />
                <span>서비스 이용 약관</span>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </div>

            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-sky-500" />
                <span>개인정보 처리방침</span>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </div>

            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <HelpCircle className="h-5 w-5 text-orange-500" />
                <span>버전 v1.0.0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8 space-y-2">
          <p className="text-sm text-gray-400">나만의 AI FRIEND</p>
          <p className="text-xs text-gray-400">
            © AIC 2025. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
