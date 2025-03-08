import React, { useState } from "react"
import { FaCog, FaArrowLeft, FaArrowRight } from "react-icons/fa" // Importing arrow icons

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(true)

  const toggleSidebar = () => {
    setIsOpen(!isOpen)
  }

  return (
    <div
      className={`h-screen bg-gray-800 text-white p-4 transition-all duration-300 ${
        isOpen ? "w-1/" : "w-0"
      }`} // Conditional class for dynamic width
    >
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">MemeCoins</h2>
        {/* Settings Icon */}
        <button onClick={() => alert("Settings Clicked")}>
          <FaCog className="text-white text-2xl cursor-pointer hover:text-gray-400" />
        </button>
      </div>
      <ul className="mt-4">
        <li className="p-2 cursor-pointer hover:bg-gray-700">Manage Another MemeCoin</li>
      </ul>
      {/* Sidebar toggle button with left/right arrows */}
      <button
        onClick={toggleSidebar}
        className="absolute bottom-4 left-1 p- rounded text-white"
      >
        {isOpen ? (
          <FaArrowLeft className="cursor-pointer hover:text-gray-400" />
        ) : (
          <FaArrowRight className="cursor-pointer hover:text-gray-400" />
        )}
      </button>
    </div>
  )
}

export default Sidebar
