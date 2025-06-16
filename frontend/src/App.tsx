import Header from "@/components/Header";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import SignUp from "./pages/SignUp";
import NotFound from "./pages/NotFound";
import CreateAiFriend from "./pages/CreateAiFriend";
import SelectMbtiPage from "./pages/SelectMbtiPage";
import ChatPage from "./pages/ChatPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import VoiceChat from "./pages/VoiceChat.tsx"; 
import { UserProvider } from "@/contexts/UserContext";
import { AiFriendProvider } from "@/contexts/AiFriendContext";

const queryClient = new QueryClient();

const App = () => {
  return (
    <UserProvider>
      <AiFriendProvider>
        <QueryClientProvider client={queryClient}>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <Header />
              <Routes>
                <Route path="/" element={<Index />} />
                <Route path="/signup" element={<SignUp />} />
                <Route path="/create-ai-friend" element={<CreateAiFriend />} />
                <Route path="/select-mbti" element={<SelectMbtiPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/chat/voicechat" element={<VoiceChat />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
                {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </QueryClientProvider>
      </AiFriendProvider>
    </UserProvider>
  );
};

export default App;
