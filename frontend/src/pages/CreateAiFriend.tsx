import { useUser } from "@/contexts/UserContext";
import { useEffect } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import axios from "axios";

// 后端API基础URL
const API_BASE_URL = "http://localhost:8181";

const CreateAiFriend = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const { user } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/signup");
    }
  }, [user, navigate]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const fileReader = new FileReader();
      fileReader.onload = () => {
        setPreviewUrl(fileReader.result as string);
      };
      fileReader.readAsDataURL(file);
    }
  };


  
  const handleCreateAiFriend = async () => {
    // If we already have a generated image, navigate to chat
    if (generatedImage) {
      navigate('/chat');
      return;
    }

    // Otherwise, generate new AI friend
    if (!selectedFile) return;
    
    setIsGenerating(true);
    try {
      // 第一步：上传照片
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('user_id', user?.uid || 'default_user');
      
      const uploadResponse = await axios.post(
        `${API_BASE_URL}/api/avatar/upload`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      if (!uploadResponse.data.success) {
        throw new Error('Failed to upload photo');
      }
      
      // 第二步：生成头像
      const generateData = new FormData();
      generateData.append('file_path', uploadResponse.data.file_path);
      generateData.append('user_id', user?.uid || 'default_user');
      
      const generateResponse = await axios.post(
        `${API_BASE_URL}/api/avatar/generate`,
        generateData
      );
      
      if (!generateResponse.data.success) {
        throw new Error('Failed to generate avatar');
      }
      
      // 设置生成的头像URL
      const avatarUrl = `${API_BASE_URL}${generateResponse.data.avatar_path}`;
      setGeneratedImage(avatarUrl);
      
      // 保存头像URL到用户上下文或本地存储，以便在聊天页面使用
      if (user) {
        localStorage.setItem(`avatar_${user.uid}`, avatarUrl);
      }
      
    } catch (error) {
      console.error('Failed to generate AI friend:', error);
      alert('头像生成失败，请重试');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">
            AI 친구의 모습을 만들어주세요!
          </h1>
          <p className="text-gray-600">
            사진을 올려주시면
            <br />
            나만의 AI 친구가 탄생해요.
          </p>
        </div>

        {/* Avatar Upload and Generated Result */}
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="flex gap-4">
            {/* Original Photo Upload */}
            <div className="w-32 h-32 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center relative">
              {previewUrl ? (
                <img src={previewUrl} alt="Selected profile" className="w-full h-full object-cover rounded-lg" />
              ) : (
                <div className="text-center">
                  <div className="text-gray-400 mb-2">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="mx-auto">
                      <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" />
                      <path d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z" />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-500">사진 업로드</span>
                </div>
              )}
              <input 
                type="file" 
                id="avatar-upload" 
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                accept="image/*" 
                onChange={handleFileChange}
              />
            </div>

            {/* Generated AI Friend Photo */}
            <div className="w-32 h-32 bg-gray-100 rounded-lg border-2 border-gray-300 flex items-center justify-center relative overflow-hidden">
              {isGenerating ? (
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              ) : generatedImage ? (
                <img src={generatedImage} alt="Generated AI friend" className="w-full h-full object-cover rounded-lg" />
              ) : (
                <div className="text-center text-gray-400">
                  <span className="text-sm">AI 친구</span>
                </div>
              )}
            </div>

          </div>
          <p className="text-sm text-gray-400">
            얼굴이 잘 보이는 정면 사진을 올려주세요.
          </p>
        </div>



        {/* Name Input */}
        <div className="mt-8">
          <div className="text-center">
            <span className="text-gray-600">친구 이름</span>
            <span className="text-gray-400 text-sm ml-2">(선택)</span>
          </div>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름을 입력하세요"
            className="w-full mt-2 p-3 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-400"
          />
        </div>

        {/* Create Button */}
        <Button 
          className={`w-full py-4 ${!selectedFile ? 'bg-gray-300' : 'bg-amber-400 hover:bg-amber-500'} text-black font-medium mt-8 relative transition-colors`}
          onClick={handleCreateAiFriend}
          disabled={isGenerating || !selectedFile}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin mr-2 inline-block" />
              생성중...
            </>
          ) : generatedImage ? (
            '채팅 시작하기'
          ) : (
            '나만의 AI친구 만들기'
          )}
        </Button>
      </div>
    </div>
  );
};

export default CreateAiFriend;
