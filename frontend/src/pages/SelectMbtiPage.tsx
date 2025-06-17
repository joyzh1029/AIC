// frontend/src/pages/SelectMbtiPage.tsx
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useMBTITypes } from "@/hooks/use-mbti-types";
import { Skeleton } from "@/components/ui/skeleton";

const SelectMbtiPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mbtiTypes, relationshipTypes, isLoading, error } = useMBTITypes();

  const [userMbti, setUserMbti] = useState<string | null>(null);
  const [relationshipType, setRelationshipType] = useState<string | null>(null);
  const [aiName, setAiName] = useState<string | null>(null);
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);

  useEffect(() => {
    // 이전 페이지에서 전달된 AI 친구 정보 (query params 또는 localStorage)
    const queryParams = new URLSearchParams(location.search);
    const nameFromQuery = queryParams.get('ai_name');
    const imageFromQuery = queryParams.get('generated_image');

    const nameFromStorage = localStorage.getItem('ai_friend_name');
    const imageFromStorage = localStorage.getItem('ai_friend_image');

    // 쿼리 파라미터가 우선, 없으면 로컬 스토리지
    const finalAiName = nameFromQuery || nameFromStorage;
    const finalGeneratedImage = imageFromQuery || imageFromStorage;

    if (finalAiName) setAiName(finalAiName);
    if (finalGeneratedImage) setGeneratedImageUrl(finalGeneratedImage);

    // AI 친구 정보가 없으면 이전 페이지로 돌아가기
    if (!finalAiName || !finalGeneratedImage) {
        toast.error("AI 친구 정보가 없습니다. 다시 생성해주세요.");
        navigate('/create-ai-friend');
    }
  }, [location, navigate]);

  const handleStartChat = () => {
    if (!userMbti || !relationshipType) {
      toast.error("당신의 MBTI와 AI 친구와의 관계 유형을 모두 선택해주세요.");
      return;
    }

    // AI 친구 정보와 사용자 선택 정보를 함께 /chat 페이지로 전달
    navigate(`/chat?user_mbti=${userMbti}&relationship_type=${relationshipType}&ai_name=${aiName || ''}&generated_image=${generatedImageUrl || ''}`);
  };

  if (error) {
    toast.error("MBTI 유형을 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.");
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-red-600">오류가 발생했습니다</h1>
          <p className="text-gray-600">{error}</p>
          <Button onClick={() => window.location.reload()}>다시 시도</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">
            어떤 친구를 원하시나요?
          </h1>
          <p className="text-gray-600">
            당신의 MBTI와 원하는 관계 유형을 선택하면,
            <br />
            더 잘 맞는 친구를 만날 수 있어요.
          </p>
        </div>

        {/* AI Friend Preview */}
        {aiName && generatedImageUrl && (
          <div className="flex flex-col items-center justify-center space-y-2">
            <img src={generatedImageUrl} alt={`${aiName}의 아바타`} className="w-24 h-24 rounded-full object-cover border-2 border-amber-400" />
            <p className="text-lg font-semibold">{aiName}</p>
            <p className="text-sm text-gray-500">생성된 AI 친구</p>
          </div>
        )}

        {/* User MBTI Selection */}
        <div className="space-y-2">
          <label htmlFor="user-mbti" className="block text-gray-700 font-medium text-left">
            당신의 MBTI는 무엇인가요?
          </label>
          {isLoading ? (
            <Skeleton className="w-full h-10" />
          ) : (
            <Select onValueChange={setUserMbti} value={userMbti || undefined}>
              <SelectTrigger id="user-mbti" className="w-full">
                <SelectValue placeholder="MBTI를 선택하세요" />
              </SelectTrigger>
              <SelectContent>
                {mbtiTypes.map((mbti) => (
                  <SelectItem key={mbti} value={mbti}>
                    {mbti}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Relationship Type Selection */}
        <div className="space-y-2">
          <label htmlFor="relationship-type" className="block text-gray-700 font-medium text-left">
            어떤 관계를 원하시나요?
          </label>
          {isLoading ? (
            <Skeleton className="w-full h-10" />
          ) : (
            <Select onValueChange={setRelationshipType} value={relationshipType || undefined}>
              <SelectTrigger id="relationship-type" className="w-full">
                <SelectValue placeholder="관계 유형을 선택하세요" />
              </SelectTrigger>
              <SelectContent>
                {relationshipTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Start Chat Button */}
        <Button 
          className={`w-full py-4 ${(!userMbti || !relationshipType || isLoading) ? 'bg-gray-300' : 'bg-amber-400 hover:bg-amber-500'} text-black font-medium mt-8 relative transition-colors`}
          onClick={handleStartChat}
          disabled={!userMbti || !relationshipType || isLoading}
        >
          {isLoading ? '로딩 중...' : 'AI 친구와 대화 시작하기'}
        </Button>
      </div>
    </div>
  );
};

export default SelectMbtiPage;