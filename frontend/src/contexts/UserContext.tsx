import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User } from "firebase/auth";

type UserContextType = {
  user: User | null;
  setUser: (user: User | null) => void;
};

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const mockUser = {
    uid: "test-user-123",
    email: "test@example.com",
    displayName: "Test User",
    photoURL: null,
    emailVerified: true,
    isAnonymous: false,
    metadata: {},
    providerData: [],
    refreshToken: "mock-refresh-token",
    tenantId: null,
    delete: async () => {},
    getIdToken: async () => "mock-id-token",
    getIdTokenResult: async () => ({ token: "mock-token", claims: {}, expirationTime: "", authTime: "", issuedAtTime: "", signInProvider: null, signInSecondFactor: null }),
    reload: async () => {},
    toJSON: () => ({})
  } as User;

  const [user, setUser] = useState<User | null>(mockUser);

  useEffect(() => {
    console.log("Firebase authentication disabled for testing. Using mock user.");
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) throw new Error("useUser must be used within UserProvider");
  return context;
}