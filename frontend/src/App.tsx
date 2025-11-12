import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Tabs from "./components/Tabs";
import UploadPage from "./modules/upload/UploadPage";
import WebcamPage from "./modules/webcam/WebCamPage";
import LivePage from "./modules/Youtube/YoutubePage";


const App: React.FC = () => {
  return (
    <Router>
      <Navbar />
      <Tabs />
      <div className="container">
        <Routes>
          <Route path="/" element={<Navigate to="/upload" />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/webcam" element={<WebcamPage />} />
          <Route path="/youtube" element={<LivePage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;