// 测试模式：移除真实Firebase初始化，使用模拟对象

// 模拟的Firebase Auth对象
// 创建一个模拟的Auth对象，实现必要的方法
// 这个对象将替代真实的Firebase Auth

const mockAuthUser = {
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
};

// 模拟的Auth对象
export const auth = {
  currentUser: mockAuthUser,
  signInWithEmailAndPassword: async () => ({ user: mockAuthUser }),
  createUserWithEmailAndPassword: async () => ({ user: mockAuthUser }),
  signOut: async () => {},
  onAuthStateChanged: (callback: any) => {
    // 立即调用回调函数，传入模拟用户
    setTimeout(() => callback(mockAuthUser), 0);
    // 返回一个空函数作为取消订阅函数
    return () => {};
  }
};

// 模拟的GoogleAuthProvider
export const googleProvider = {
  addScope: () => {}
};
