import { useState } from "react";

export default function About() {
  const [highlight, setHighlight] = useState("");

  const features = [
    { title: "What We Are", description: "SafeRide is an AI-powered platform designed to improve road safety by automating traffic violation detection." },
    { title: "Why We Created It", description: "To address the limitations of manual traffic monitoring and reduce accidents caused by unsafe driving behaviors." },
    { title: "How It Works", description: "Using AI and smart algorithms, SafeRide analyzes traffic patterns to provide faster, unbiased, and scalable enforcement." },
  ];

  return (
    <div className="p-8 text-center bg-gradient-to-r from-blue-50 to-indigo-50 min-h-screen flex flex-col justify-center items-center">
      <h2 className="text-3xl font-bold mb-6 text-indigo-800 animate-pulse">About Us</h2>

      <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-3 max-w-5xl w-full">
        {features.map((feature, index) => (
          <div
            key={index}
            onMouseEnter={() => setHighlight(feature.title)}
            onMouseLeave={() => setHighlight("")}
            className={`p-6 rounded-xl shadow-lg transition-transform transform hover:scale-105 hover:shadow-2xl bg-white`}
          >
            <h3 className={`text-xl font-semibold mb-2 ${highlight === feature.title ? "text-indigo-600" : "text-gray-800"}`}>
              {feature.title}
            </h3>
            <p className="text-gray-600">{feature.description}</p>
          </div>
        ))}
      </div>

      <p className="mt-10 text-gray-700 font-semibold animate-fadeIn">
        Creators: Sakshi Kadam, Priyanka Barman, Radhika Pradhan, Tejas Deshmukh
      </p>
    </div>
  );
}
