
import React from 'react';
import { User, MessageSquare, Heart } from 'lucide-react';

interface FeatureCardProps {
  icon: "avatar" | "chat" | "support";
  title: string;
  description: string;
  iconColor: string;
}

const FeatureCard = ({ icon, title, description, iconColor }: FeatureCardProps) => {
  const renderIcon = () => {
    switch (icon) {
      case "avatar":
        return <User className="w-5 h-5 text-sky-500" />;
      case "chat":
        return <MessageSquare className="w-5 h-5 text-amber-500" />;
      case "support":
        return <Heart className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100">
      <div className={`w-12 h-12 rounded-full ${iconColor} flex items-center justify-center mb-6`}>
        {renderIcon()}
      </div>
      <h3 className="text-xl font-bold mb-4">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
};

export default FeatureCard;
