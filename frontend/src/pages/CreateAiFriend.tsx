
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const characterOptions = [
  { id: 1, icon: "👤", label: "기본" },
  { id: 2, icon: "🌟", label: "활발한" },
  { id: 3, icon: "😊", label: "따뜻한" },
  { id: 4, icon: "😄", label: "즐거운" },
];

const CreateAiFriend = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedCharacter, setSelectedCharacter] = useState<number | null>(null);
  const [name, setName] = useState("");
  const navigate = useNavigate();

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

  const handleCharacterSelect = (id: number) => {
    setSelectedCharacter(id);
  };
  
  const handleCreateAiFriend = () => {
    // Navigate to the chat page
    navigate('/chat');
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">
            AI 친구의 모습을 만들어주세요!
          </h1>
          <p className="text-gray-600">
            어린 시절 사진을 올려주시면
            <br />
            나만의 AI 친구가 탄생해요.
          </p>
        </div>

        {/* Avatar Upload */}
        <div className="flex flex-col items-center justify-center space-y-4">
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
          <p className="text-sm text-gray-400">
            얼굴이 잘 보이는 정면 사진을 올려주세요.
          </p>
        </div>

        <div className="text-center text-gray-500 text-sm mt-8">
          <span>또는</span>
          <p className="mt-4">기본 아바타 스타일을 선택해보세요</p>
        </div>

        {/* Character Selection */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          {characterOptions.map((option) => (
            <button 
              key={option.id}
              onClick={() => handleCharacterSelect(option.id)}
              className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl ${selectedCharacter === option.id ? 'bg-blue-100' : 'bg-gray-100'}`}
            >
              {option.icon}
            </button>
          ))}
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
          className="w-full py-4 bg-amber-400 hover:bg-amber-500 text-black font-medium mt-8"
          onClick={handleCreateAiFriend}
        >
          내 친구 만들기
        </Button>
      </div>
    </div>
  );
};

export default CreateAiFriend;
