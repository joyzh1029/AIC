import React, { createContext, useContext, useState } from "react";

const AiFriendContext = createContext<any>(null);

export const AiFriendProvider = ({ children }: { children: React.ReactNode }) => {
  const [aiFriendName, setAiFriendName] = useState("");
  const [aiFriendImage, setAiFriendImage] = useState<string | null>(null);

  return (
    <AiFriendContext.Provider value={{ aiFriendName, setAiFriendName, aiFriendImage, setAiFriendImage }}>
      {children}
    </AiFriendContext.Provider>
  );
};

export const useAiFriend = () => useContext(AiFriendContext);