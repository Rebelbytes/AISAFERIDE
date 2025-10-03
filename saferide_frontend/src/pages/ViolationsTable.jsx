import { useState, useEffect } from "react";
import api from "../utils/api";

export default function ViolationsTable({ videoFile }) {
  const [violations, setViolations] = useState([]);

  useEffect(() => {
    const fetchViolations = async () => {
      if (videoFile) {
        // Upload video and get violations from it
        const formData = new FormData();
        formData.append("file", videoFile);

        try {
          const res = await api.post("/api/detect/", formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });

          setViolations(res.data.violations || res.data); // normalize response
        } catch (error) {
          console.error("Error fetching violations:", error);
        }
      } else {
        // Fetch all violations
        try {
          const res = await api.get("/api/violations/");
          setViolations(res.data.violations || res.data);
        } catch (error) {
          console.error("Error fetching all violations:", error);
        }
      }
    };

    fetchViolations();
  }, [videoFile]);

  if (!violations || violations.length === 0) {
    return <div>No violations found.</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Detected Violations</h2>
      <table className="table-auto w-full border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-4 py-2">#</th>
            <th className="border px-4 py-2">Violation Label</th>
            <th className="border px-4 py-2">Violation Image</th>
          </tr>
        </thead>
        <tbody>
          {violations.map((violation, index) => (
            <tr key={index} className="text-center">
              <td className="border px-4 py-2">{index + 1}</td>
              <td className="border px-4 py-2">{violation.violation_type}</td>
              <td className="border px-4 py-2">
                <img
                  src={`http://127.0.0.1:8000/media/${violation.frame_image}`}
                  alt={violation.violation_type}
                  className="w-32 h-32 object-cover mx-auto rounded"
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
