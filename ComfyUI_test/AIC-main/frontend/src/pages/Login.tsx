import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import AiFriendLogo from "@/components/AiFriendLogo";
import { Link } from "react-router-dom";

const Login = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-100 via-white to-rose-100 flex">
      {/* Left Section - Image and Text */}
      <div className="w-1/2 p-12 flex flex-col justify-center items-start text-left pl-24">
        <div className="relative w-80 h-96 mb-8">
          <img 
            src="/images/login-character.png" 
            alt="Character" 
            className="absolute top-0 left-0 w-64 h-80 object-cover"
          />
          <div className="absolute top-12 right-0 w-48 h-64 bg-amber-50 rounded-lg border border-amber-200 p-4 flex items-center justify-center">
            <img 
              src="/images/pixel-character.png" 
              alt="Pixel Character" 
              className="w-32 h-32 object-contain"
            />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold mb-4">
          나의 어린 시절 모습으로<br />
          만나는 특별한 AI 친구
        </h2>
        <p className="text-gray-600 text-sm leading-relaxed">
          나의 사진과 프롬프트로 만들어진 친구와 다양한 방식으로<br />
          교감하며 감사한 순간들을 성장하는 계기 삼을 수 있는<br />
          힐링 서비스
        </p>
      </div>

      {/* Right Section - Login Form */}
      <div className="w-1/2 p-12 flex flex-col items-center justify-center">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-center mb-8">
            <AiFriendLogo />
            <span className="ml-2 text-xl">My AI Chingu</span>
          </div>

          <h1 className="text-2xl font-bold text-center mb-8">환영합니다</h1>
          <p className="text-gray-600 text-center text-sm mb-8">
            계정에 로그인하고 AI 친구를 만나보세요
          </p>

          <div className="space-y-6">
            <div>
              <label className="text-sm text-gray-600">이메일</label>
              <Input 
                type="email" 
                placeholder="이메일 주소를 입력하세요" 
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-sm text-gray-600">비밀번호</label>
              <Input 
                type="password" 
                placeholder="비밀번호를입력하세요" 
                className="mt-1"
              />
            </div>

            <div className="flex items-center">
              <input type="checkbox" className="rounded border-gray-300" />
              <label className="ml-2 text-sm text-gray-600">자동 로그인</label>
              <a href="#" className="ml-auto text-sm text-gray-400 hover:text-gray-600">비밀번호찾기</a>
            </div>

            <Button className="w-full bg-sky-400 hover:bg-sky-500 text-white py-6">
              로그인
            </Button>

            <div className="text-center text-sm text-gray-600">
              간편 로그인
            </div>

            <div className="flex justify-center space-x-4">
              <button className="w-12 h-12 rounded-full border border-gray-200 flex items-center justify-center">
                G
              </button>
              <button className="w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center">
                N
              </button>
              <button className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-600 to-pink-500 text-white flex items-center justify-center">
                <span className="text-lg">in</span>
              </button>
            </div>

            <div className="text-center text-sm">
              <span className="text-gray-600">아직 계정이 없으신가요? </span>
              <Link to="/signup" className="text-rose-400 hover:text-rose-500">회원가입</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
