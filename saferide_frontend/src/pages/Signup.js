// src/pages/Signup.js
import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FaIdBadge, FaUser, FaBuilding, FaMapMarkerAlt, FaEnvelope, FaLock, FaShieldAlt } from "react-icons/fa";
import api from "../utils/api";

export default function Signup() {
  const [form, setForm] = useState({
    officer_id: "",
    officer_name: "",
    batch: "",
    location: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("register/", form);
      setMessage("✅ Signup successful! Redirecting...");
      setTimeout(() => (window.location.href = "/login"), 1500);
    } catch (err) {
      console.error(err.response?.data);
      setMessage("❌ " + (err.response?.data?.error || "Error while signing up. Try again!"));
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { name: "officer_id", placeholder: "Enter Officer ID (e.g., OF12345)", icon: <FaIdBadge /> },
    { name: "officer_name", placeholder: "Full Name", icon: <FaUser /> },
    { name: "batch", placeholder: "Batch (e.g., 2025A)", icon: <FaBuilding /> },
    { name: "location", placeholder: "Station Location", icon: <FaMapMarkerAlt /> },
    { name: "email", placeholder: "Email Address", type: "email", icon: <FaEnvelope /> },
    { name: "password", placeholder: "Password", type: "password", icon: <FaLock /> },
  ];

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-r from-blue-500 via-teal-400 to-green-400 overflow-hidden relative">
      {/* Animated Police Badge Background */}
      <motion.div
        className="absolute top-0 left-0 w-full h-full opacity-10"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 120, ease: "linear" }}
      >
        <FaShieldAlt size={400} className="text-white mx-auto mt-20 opacity-20" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: -50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="bg-white p-10 rounded-3xl shadow-2xl w-96 relative z-10"
      >
        <h2 className="text-3xl font-bold mb-6 text-center text-gray-800 flex items-center justify-center gap-2">
          <FaShieldAlt className="text-blue-600 animate-bounce" /> Officer Signup
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((field) => (
            <div key={field.name} className="relative">
              <span className="absolute top-3 left-3 text-gray-400">{field.icon}</span>
              <input
                name={field.name}
                type={field.type || "text"}
                placeholder={field.placeholder}
                value={form[field.name]}
                onChange={handleChange}
                required
                className="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 transition shadow-sm hover:shadow-md"
              />
            </div>
          ))}

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg font-semibold text-white transition ${
              loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Signing up..." : "Signup"}
          </motion.button>
        </form>

        {/* Success / Error messages */}
        {message && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`mt-4 text-center font-medium ${
              message.startsWith("✅") ? "text-green-600" : "text-red-600"
            }`}
          >
            {message}
          </motion.p>
        )}

        {/* Extra link */}
        <div className="mt-6 text-center text-gray-700">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 font-semibold hover:underline">
            Login
          </Link>
        </div>
      </motion.div>
    </div>
  );
}


