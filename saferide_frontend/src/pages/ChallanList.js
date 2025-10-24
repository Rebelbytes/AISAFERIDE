import React, { useEffect, useState } from "react";
import axios from "axios";

const ChallanList = () => {
  const [challans, setChallans] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/api/challan/all/")
      .then((res) => setChallans(res.data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h2 className="text-3xl font-bold mb-6 text-center">All Challans</h2>

      <div className="bg-white shadow-lg rounded-xl p-4">
        <table className="w-full table-auto border-collapse">
          <thead>
            <tr className="bg-blue-600 text-white">
              <th className="p-2">Vehicle</th>
              <th className="p-2">Owner</th>
              <th className="p-2">Violation</th>
              <th className="p-2">Fine</th>
              <th className="p-2">Status</th>
              <th className="p-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {challans.map((c) => (
              <tr key={c.id} className="border-b text-center">
                <td className="p-2">{c.owner_vehicle_number}</td>
                <td className="p-2">{c.owner_name}</td>
                <td className="p-2 capitalize">{c.violation_type.replace("_", " ")}</td>
                <td className="p-2">₹{c.fine_amount}</td>
                <td className="p-2">{c.status}</td>
                <td className="p-2">{new Date(c.date_issued).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ChallanList;
