import React, { useState } from "react";
import { FaCog, FaArrowLeft, FaArrowRight } from "react-icons/fa"; // Importing arrow icons

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(true);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div
      className={`h-screen bg-gray-900 text-white transition-all duration-300 border-r border-gray-700 ${
        isOpen ? "w-64" : "w-16"
      }`}
    >
      <div className="flex justify-between items-center p-6 border-b border-gray-700">
        <button
          onClick={toggleSidebar}
          className="text-gray-400 hover:text-white transition-colors duration-200"
        >
          {isOpen ? <FaArrowLeft /> : <FaArrowRight />}
        </button>
        
        {isOpen && (
          <h2 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            Curtis Portal
          </h2>
        )}

        {isOpen && (
          <button 
            onClick={() => alert("Settings Clicked")}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <FaCog />
          </button>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
