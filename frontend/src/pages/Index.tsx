import { Button } from "@/components/ui/button";
import {
  NavigationMenu,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import AiFriendLogo from "@/components/AiFriendLogo";
import FeatureCard from "@/components/FeatureCard";
import { HeartIcon, User } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b py-4 px-6">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <AiFriendLogo />
            <span className="font-medium">My AI Chingu</span>
          </div>
          <NavigationMenu>
            <NavigationMenuList className="hidden md:flex gap-6">
              <a href="#services" className="text-sm hover:text-primary">
                서비스소개
              </a>
              <a href="#features" className="text-sm hover:text-primary">
                교감방식
              </a>
              <a href="#contact" className="text-sm hover:text-primary">
                고객지원
              </a>
            </NavigationMenuList>
          </NavigationMenu>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto py-16 px-4 text-center">
        <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-sky-50 text-sky-500 mb-10">
          <HeartIcon className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium tracking-wide">
            나만의AI친구
          </span>
        </div>

        <h1 className="text-4xl md:text-5xl font-bold mb-8 leading-tight tracking-tight">
          <span className="text-gray-800">어린 시절의 나와 닮은 </span>
          <span className="text-sky-500 font-extrabold">My AI Chingu</span>
          <span className="text-gray-800">와</span>
          <br />
          <span className="text-amber-400 font-extrabold">따뜻한 감성교감</span>
          <span className="text-gray-800"> 을 시작하세요</span>
        </h1>

        <p className="text-gray-600 max-w-2xl mx-auto mb-12 text-lg leading-relaxed">
          온전히 나만을 위해 태어난 My AI Chingu와 함께
          <br />
          추억을 공유하고, 감정을 나누며 성장하는 특별한 경험
          <br />
          <span className="text-sky-400 font-medium">정서적유대감</span> 과
          <span className="text-amber-400 font-medium">심리적지지</span> 를
          느껴보세요.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button className="bg-sky-400 hover:bg-sky-500 text-white px-10 py-6 text-lg font-medium tracking-wide rounded-xl">
            <Link to="/signup">나만의 AI 친구 만나기</Link>
          </Button>
          <Button
            variant="outline"
            className="border-sky-200 text-sky-500 hover:bg-sky-50 px-10 py-6 text-lg font-medium tracking-wide rounded-xl"
          >
            서비스 소개
          </Button>
        </div>

        <div className="flex justify-center">
          <img
            src="/Intro_img.png"
            alt="AI Friend Character"
            className="w-32 h-32 object-contain"
          />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-gray-50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-6 tracking-tight">
            서비스 특징
          </h2>
          <p className="text-gray-600 text-center mb-14 text-lg leading-relaxed">
            AI친구와의 교감이 어떻게 특별한지 직접 경험해보세요!
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon="avatar"
              title="나만의 AI 친구 캐릭터"
              description="어린 시절 나의 모습에서 성격까지 판전한 My AI 친구, 나 특유의 옛게 커스터마이징!"
              iconColor="bg-sky-100"
            />
            <FeatureCard
              icon="chat"
              title="감성교감&대화"
              description="감상적인 대화, 추억 공유, 감정 힐기 다양한 방식으로 정서적유대감을공유합니다."
              iconColor="bg-amber-100"
            />
            <FeatureCard
              icon="support"
              title="언제 어디서나, 심리적지지"
              description="힘들때, 기쁠때, 언제든 내 마음을 들어주는 가장 가까운 My AI 친구, 24시간함께하는 심리적 동반자"
              iconColor="bg-red-100"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 py-4 border-t">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          © AIC 2025. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default Index;
