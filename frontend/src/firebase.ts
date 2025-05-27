// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
/*import { getAnalytics } from "firebase/analytics";*/
import { getAuth, GoogleAuthProvider } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyC4U0jBzfjMCoaFRszxeQMu_5awpuI26lA",
  authDomain: "my-ai-friend-d27f7.firebaseapp.com",
  projectId: "my-ai-friend-d27f7",
  storageBucket: "my-ai-friend-d27f7.firebasestorage.app",
  messagingSenderId: "184489961423",
  appId: "1:184489961423:web:8de7726c6eaf148c2154ba",
  measurementId: "G-1CLN78QMQH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
/* const analytics = getAnalytics(app); */
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();