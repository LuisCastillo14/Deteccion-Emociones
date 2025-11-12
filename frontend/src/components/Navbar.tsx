import React from "react";

const Navbar: React.FC = () => {
  return (
    <nav className="navbar navbar-custom px-3 d-flex justify-content-between align-items-center">
      <div className="d-flex align-items-center">
        <img
          src="logo.png"
          alt="EmotiScan"
          style={{ width: "30px", marginRight: "10px" }}
        />
        <span className="navbar-brand">EmotiScan</span>
      </div>
      <span className="subtitle">Escaneo de emociones en tiempo real</span>
    </nav>
  );
};

export default Navbar;
