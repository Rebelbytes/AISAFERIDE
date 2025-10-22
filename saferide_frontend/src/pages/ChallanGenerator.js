import React, { useState } from "react";
import axios from "axios";

const ChallanGenerator = () => {
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [violation, setViolation] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResponse(null);

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/challan/generate/", {
        vehicle_number: vehicleNumber,
        violation: violation,
      });

      setResponse(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Error generating challan");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-8">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-center">E-Challan Generator</h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Enter Vehicle Number (e.g., MH12AB1234)"
            value={vehicleNumber}
            onChange={(e) => setVehicleNumber(e.target.value)}
            className="p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            required
          />

          <select
            value={violation}
            onChange={(e) => setViolation(e.target.value)}
            className="p-2 border rounded-lg"
            required
          >
            <option value="">Select Violation</option>
            <option value="no_helmet">No Helmet</option>
            <option value="signal_jump">Signal Jump</option>
            <option value="no_seatbelt">No Seatbelt</option>
            <option value="triple_riding">Triple Riding</option>
          </select>

          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg"
          >
            Generate Challan
          </button>
        </form>

        {response && (
          <div className="mt-6 p-4 bg-green-100 text-green-800 rounded-lg">
            <h3 className="font-bold mb-2">Challan Generated ✅</h3>
            <p><strong>Owner:</strong> {response.owner_name}</p>
            <p><strong>Fine:</strong> ₹{response.fine_amount}</p>
            <p><strong>Status:</strong> Pending</p>
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-100 text-red-800 rounded-lg">
            ❌ {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChallanGenerator;
