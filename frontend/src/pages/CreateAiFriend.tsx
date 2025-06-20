import { useUser } from "@/contexts/UserContext";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import axios from "axios";
import { useAiFriend } from "@/contexts/AiFriendContext";

// 后端API基础URL
const API_BASE_URL = "http://localhost:8181";

const CreateAiFriend = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [storedImageUrl, setStoredImageUrl] = useState<string | null>(null);
  const [userData, setUserData] = useState<any>(null);
  const [result, setResult] = useState<string | null>(null);

  const { user } = useUser();
  const navigate = useNavigate();
  const { aiFriendName, setAiFriendName, aiFriendImage, setAiFriendImage } =
    useAiFriend();

  // 채팅 시작 가능 여부 확인
  const canStartChat = !!generatedImage || !!storedImageUrl;
  const canStartChatButton = !!selectedFile || !!storedImageUrl;

  // 로그인 체크
  useEffect(() => {
    if (!user) {
      navigate("/signup");
    }
  }, [user, navigate]);

  // 로그인 후 Firestore에서 이미지 URL 불러오기 (ComfyUI)
  useEffect(() => {
    const fetchAiFriendImage = async () => {
      if (!user?.email) return;
      try {
        const response = await axios.get(
          `${API_BASE_URL}/get_user_data?user_id=${encodeURIComponent(
            user.email
          )}`
        );
        if (response.data) {
          setUserData(response.data);
          setStoredImageUrl(response.data.profile_image_url);
          console.log("프로필 이미지 URL:", response.data.profile_image_url);
        }
      } catch (e) {
        setUserData(null);
      }
    };
    fetchAiFriendImage();
  }, [user]);

  // 이미지가 생성되거나 불러올 때 setAiFriendImage로 저장
  useEffect(() => {
    if (generatedImage) {
      setAiFriendImage(generatedImage);
    } else if (storedImageUrl) {
      setAiFriendImage(storedImageUrl);
    }
  }, [generatedImage, storedImageUrl, setAiFriendImage]);

  // 디버깅 로그 (ComfyUI)
  useEffect(() => {
    console.log("canStartChat:", canStartChat);
    console.log("generatedImage:", !!generatedImage);
    console.log("canStartChatButton:", canStartChatButton);
    console.log("isGenerating:", isGenerating);
    console.log("selectedFile:", selectedFile);
    console.log("storedImageUrl:", storedImageUrl);
  }, [
    canStartChat,
    generatedImage,
    canStartChatButton,
    isGenerating,
    selectedFile,
    storedImageUrl,
  ]);

  // 파일 선택 핸들러
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const fileReader = new FileReader();
      fileReader.onload = () => {
        setPreviewUrl(fileReader.result as string);
      };
      fileReader.readAsDataURL(file);
      setStoredImageUrl(null); // 새 파일 선택 시 저장된 이미지 URL 초기화
    }
  };

  // Base64를 Blob으로 변환 (ComfyUI)
  function base64ToBlob(base64: string, mime = "image/png") {
    const byteString = atob(base64.split(",")[1] || base64);
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mime });
  }

  // RAG 방식 AI 친구 생성
  const generateWithRAG = async () => {
    if (!selectedFile) return;

    try {
      // 1단계: 사진 업로드
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("user_id", user?.uid || "default_user");

      const uploadResponse = await axios.post(
        `${API_BASE_URL}/api/avatar/upload`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      if (!uploadResponse.data.success) {
        throw new Error("Failed to upload photo");
      }

      // 2단계: 아바타 생성
      const generateData = new FormData();
      generateData.append("file_path", uploadResponse.data.file_path);
      generateData.append("user_id", user?.uid || "default_user");

      const generateResponse = await axios.post(
        `${API_BASE_URL}/api/avatar/generate`,
        generateData
      );

      if (!generateResponse.data.success) {
        throw new Error("Failed to generate avatar");
      }

      // 생성된 아바타 URL 설정
      const avatarUrl = `${API_BASE_URL}${generateResponse.data.avatar_path}`;
      setGeneratedImage(avatarUrl);

      // localStorage에 저장 (RAG)
      if (user) {
        localStorage.setItem(`avatar_${user.uid}`, avatarUrl);
      }
    } catch (error) {
      console.error("RAG 방식 생성 실패:", error);
      throw error;
    }
  };

  // ComfyUI 방식 AI 친구 생성
  const generateWithComfyUI = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const response = await axios.post(
        "http://localhost:8181/wanna-image/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      if (response.data && response.data.image_url) {
        setGeneratedImage(response.data.image_url);
      } else if (response.data && response.data.base64_image) {
        setGeneratedImage(
          `data:image/png;base64,${response.data.base64_image}`
        );
      } else {
        setGeneratedImage(previewUrl);
      }
      setResult(JSON.stringify(response.data));
    } catch (error) {
      console.error("ComfyUI 방식 생성 실패:", error);
      throw error;
    }
  };

  // AI 친구 생성 메인 핸들러
  const handleCreateAiFriend = async () => {
    // 이미 생성된 이미지가 있으면 채팅으로 이동
    if (generatedImage) {
      navigate("/select-mbti");
      return;
    }

    if (!selectedFile) return;

    setIsGenerating(true);
    setResult(null);

    try {
      // 환경에 따라 적절한 생성 방식 선택
      // RAG 서버가 실행 중인지 먼저 확인
      try {
        await axios.get(`${API_BASE_URL}/health`);
        await generateWithRAG();
      } catch {
        // RAG 서버가 응답하지 않으면 ComfyUI 방식 사용
        await generateWithComfyUI();
      }
    } catch (error: any) {
      console.error("AI 친구 생성 실패:", error);
      alert("아바타 생성에 실패했습니다. 다시 시도해주세요.");
      setResult(
        "업로드 실패: " + (error.response?.data?.error || error.message)
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // 채팅 시작 핸들러
  const handleStartChat = async () => {
    if (!storedImageUrl && generatedImage) {
      // ComfyUI 방식: 생성된 이미지 저장
      const blob = base64ToBlob(generatedImage, "image/png");
      const file = new File([blob], "ai_friend.png", { type: "image/png" });

      const formData = new FormData();
      formData.append("image", file);
      formData.append("user_id", user?.email || "user_info");
      formData.append("name", name);

      try {
        const response = await axios.post(
          "http://localhost:8181/save_ai_friend_image/",
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        console.log("이미지 저장 성공:", response.data);
      } catch (error: any) {
        console.error("이미지 저장 실패:", error);
      }
    }

    // 채팅 페이지로 이동
    navigate("/select-mbti");
  };

  // 버튼 클릭 핸들러
  const handleButtonClick = () => {
    if (canStartChat) {
      handleStartChat();
    } else if (selectedFile && !storedImageUrl && !generatedImage) {
      handleCreateAiFriend();
    } else if (storedImageUrl) {
      handleStartChat();
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">AI 친구의 모습을 만들어주세요!</h1>
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
                <img
                  src={previewUrl}
                  alt="Selected profile"
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <div className="text-center">
                  <div className="text-gray-400 mb-2">
                    <svg
                      width="40"
                      height="40"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      className="mx-auto"
                    >
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
                <img
                  src={generatedImage}
                  alt="Generated AI friend"
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : storedImageUrl ? (
                <img
                  src={storedImageUrl}
                  alt="Stored AI friend"
                  className="w-full h-full object-cover rounded-lg"
                />
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
            onChange={(e) => {
              setName(e.target.value);
              setAiFriendName(e.target.value); // 전역 상태에도 저장
            }}
            placeholder="이름을 입력하세요"
            className="w-full mt-2 p-3 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-400"
          />
        </div>

        {/* Create Button */}
        <Button
          className={`w-full py-4 ${
            !canStartChatButton
              ? "bg-gray-300"
              : "bg-amber-400 hover:bg-amber-500"
          } text-black font-medium mt-8 relative transition-colors`}
          onClick={handleButtonClick}
          disabled={isGenerating || !canStartChatButton}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin mr-2 inline-block" />
              생성중...
            </>
          ) : canStartChat ? (
            "채팅 시작하기"
          ) : (
            "나만의 AI친구 만들기"
          )}
        </Button>
      </div>
    </div>
  );
};

export default CreateAiFriend;
