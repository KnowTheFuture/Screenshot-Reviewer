import useKeyboardShortcuts from "./hooks/useKeyboardShortcuts.js";
import Home from "./pages/Home.jsx";

function App() {
  useKeyboardShortcuts();
  return <Home />;
}

export default App;
