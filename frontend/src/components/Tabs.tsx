import React from "react";
import { NavLink } from "react-router-dom";

const Tabs: React.FC = () => {
  return (
    <div className="tabs-container">
      <NavLink
        to="/upload"
        className={({ isActive }) =>
          `tab-btn ${isActive ? "active" : ""}`
        }
      >
        Imagen
      </NavLink>
      <NavLink
        to="/webcam"
        className={({ isActive }) =>
          `tab-btn ${isActive ? "active" : ""}`
        }
      >
        Cámara Web
      </NavLink>
      <NavLink
        to="/youtube"
        className={({ isActive }) =>
          `tab-btn ${isActive ? "active" : ""}`
        }
      >
        YouTube
      </NavLink>
    </div>
  );
};

export default Tabs;
