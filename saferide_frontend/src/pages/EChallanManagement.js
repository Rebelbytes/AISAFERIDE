import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Download,
  Mail,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  FileText,
  Calendar,
  User,
  Car,
  DollarSign,
  MoreVertical,
  RefreshCw,
  Plus,
  ChevronDown,
  ChevronUp,
  Camera,
  Video,
  Shield,
} from "lucide-react";
import api from "../utils/api";

const statusColors = {
  Pending: "bg-yellow-100 text-yellow-800",
  Paid: "bg-green-100 text-green-800",
  Disputed: "bg-red-100 text-red-800",
  Cancelled: "bg-gray-100 text-gray-800",
};

const statusIcons = {
  Pending: Clock,
  Paid: CheckCircle,
  Disputed: AlertCircle,
  Cancelled: XCircle,
};

export default function EChallanManagement() {
  const [echallans, setEchallans] = useState([]);
  const [filteredEchallans, setFilteredEchallans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [violationFilter, setViolationFilter] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedEchallan, setSelectedEchallan] = useState(null);
  const [showEchallanModal, setShowEchallanModal] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEchallan, setNewEchallan] = useState({
    vehicle_number: "",
    violation_type: "",
    fine_amount: "",
    notes: "",
    created_by: "Admin"
  });

  useEffect(() => {
    fetchEchallans();
    fetchStats();
  }, []);

  useEffect(() => {
    filterEchallans();
  }, [echallans, searchTerm, statusFilter, violationFilter, dateRange]);

  const fetchEchallans = async () => {
    try {
      setLoading(true);
      const response = await api.get("/echallan/");
      setEchallans(response.data);
    } catch (error) {
      console.error("Error fetching echallans:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get("/echallan/stats/");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const filterEchallans = () => {
    let filtered = [...echallans];

    // Search by vehicle number
    if (searchTerm) {
      filtered = filtered.filter((echallan) =>
        echallan.vehicle_number.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter) {
      filtered = filtered.filter((echallan) => echallan.status === statusFilter);
    }

    // Filter by violation type
    if (violationFilter) {
      filtered = filtered.filter((echallan) =>
        echallan.violation_type.toLowerCase().includes(violationFilter.toLowerCase())
      );
    }

    // Filter by date range
    if (dateRange.start) {
      filtered = filtered.filter((echallan) => {
        const echallanDate = new Date(echallan.date_issued);
        const startDate = new Date(dateRange.start);
        return echallanDate >= startDate;
      });
    }

    if (dateRange.end) {
      filtered = filtered.filter((echallan) => {
        const echallanDate = new Date(echallan.date_issued);
        const endDate = new Date(dateRange.end);
        return echallanDate <= endDate;
      });
    }

    setFilteredEchallans(filtered);
  };

  const handleSendEmail = async (echallanId) => {
    try {
      setActionLoading({ ...actionLoading, [echallanId]: true });
      await api.post(`/echallan/${echallanId}/send-email/`);
      alert("Email sent successfully!");
    } catch (error) {
      console.error("Error sending email:", error);
      alert("Failed to send email. Please try again.");
    } finally {
      setActionLoading({ ...actionLoading, [echallanId]: false });
    }
  };

  const handleDownloadPDF = async (echallanId) => {
    try {
      setActionLoading({ ...actionLoading, [echallanId]: true });
      const response = await api.get(`/echallan/${echallanId}/download-pdf/`, {
        responseType: "blob",
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `echallan_${echallanId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading PDF:", error);
      alert("Failed to download PDF. Please try again.");
    } finally {
      setActionLoading({ ...actionLoading, [echallanId]: false });
    }
  };

  const handleStatusUpdate = async (echallanId, newStatus) => {
    try {
      setActionLoading({ ...actionLoading, [echallanId]: true });
      await api.patch(`/echallan/${echallanId}/`, { status: newStatus });
      await fetchEchallans();
      alert("Status updated successfully!");
    } catch (error) {
      console.error("Error updating status:", error);
      alert("Failed to update status. Please try again.");
    } finally {
      setActionLoading({ ...actionLoading, [echallanId]: false });
    }
  };

  const handleDeleteEchallan = async (echallanId) => {
    if (window.confirm("Are you sure you want to delete this eChallan?")) {
      try {
        setActionLoading({ ...actionLoading, [echallanId]: true });
        await api.delete(`/echallan/${echallanId}/`);
        await fetchEchallans();
        alert("EChallan deleted successfully!");
      } catch (error) {
        console.error("Error deleting echallan:", error);
        alert("Failed to delete eChallan. Please try again.");
      } finally {
        setActionLoading({ ...actionLoading, [echallanId]: false });
      }
    }
  };

  const handleCreateEchallan = async () => {
    try {
      setActionLoading({ ...actionLoading, create: true });
      await api.post("/echallan/", newEchallan);
      await fetchEchallans();
      setShowCreateModal(false);
      setNewEchallan({
        vehicle_number: "",
        violation_type: "",
        fine_amount: "",
        notes: "",
        created_by: "Admin"
      });
      alert("EChallan created successfully!");
    } catch (error) {
      console.error("Error creating echallan:", error);
      alert("Failed to create eChallan. Please try again.");
    } finally {
      setActionLoading({ ...actionLoading, create: false });
    }
  };

  const viewEchallanDetails = (echallan) => {
    setSelectedEchallan(echallan);
    setShowEchallanModal(true);
  };

  const clearFilters = () => {
    setSearchTerm("");
    setStatusFilter("");
    setViolationFilter("");
    setDateRange({ start: "", end: "" });
  };

  const getUniqueViolationTypes = () => {
    const types = [...new Set(echallans.map((echallan) => echallan.violation_type))];
    return types;
  };

  const violationTypes = [
    'No Helmet',
    'Triple Riding',
    'Right Side',
    'Wrong Side',
    'Using Mobile',
    'Vehicle No License Plate',
    'Red Light Jumping',
    'Overspeeding',
    'No Seat Belt'
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">eChallan Management</h1>
          <p className="text-gray-600">Manage traffic violation eChallans and monitor their status</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total eChallans</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_echallans}</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Clock className="w-6 h-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.pending_echallans}</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Paid</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.paid_echallans}</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Fine Amount</p>
                  <p className="text-2xl font-bold text-gray-900">₹{stats.total_fine_amount}</p>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-6">
            <div className="flex flex-col lg:flex-row gap-4 mb-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search by vehicle number..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Filter className="w-5 h-5" />
                Filters
                {showFilters ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {/* Create New */}
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create New
              </button>

              {/* Refresh */}
              <button
                onClick={fetchEchallans}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200"
              >
                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Statuses</option>
                    <option value="Pending">Pending</option>
                    <option value="Paid">Paid</option>
                    <option value="Disputed">Disputed</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>
                </div>

                {/* Violation Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Violation Type
                  </label>
                  <select
                    value={violationFilter}
                    onChange={(e) => setViolationFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Types</option>
                    {getUniqueViolationTypes().map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) =>
                        setDateRange({ ...dateRange, start: e.target.value })
                      }
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) =>
                        setDateRange({ ...dateRange, end: e.target.value })
                      }
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Clear Filters */}
            {(searchTerm || statusFilter || violationFilter || dateRange.start || dateRange.end) && (
              <div className="mt-4">
                <button
                  onClick={clearFilters}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        </div>

        {/* EChallans Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              EChallans ({filteredEchallans.length})
            </h3>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Loading eChallans...</span>
            </div>
          ) : filteredEchallans.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No eChallans found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      EChallan ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vehicle Number
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Violation Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fine Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Issue Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredEchallans.map((echallan) => {
                    const StatusIcon = statusIcons[echallan.status];
                    return (
                      <tr key={echallan.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          #{echallan.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <Car className="w-4 h-4 text-gray-400 mr-2" />
                            {echallan.vehicle_number}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <User className="w-4 h-4 text-gray-400 mr-2" />
                            {echallan.owner?.owner_name || "N/A"}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {echallan.violation_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <DollarSign className="w-4 h-4 text-gray-400 mr-1" />
                            ₹{echallan.fine_amount}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[echallan.status]}`}
                          >
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {echallan.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                            {new Date(echallan.date_issued).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => viewEchallanDetails(echallan)}
                              className="text-blue-600 hover:text-blue-900 p-1 rounded"
                              title="View Details"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleSendEmail(echallan.id)}
                              disabled={actionLoading[echallan.id]}
                              className="text-green-600 hover:text-green-900 p-1 rounded disabled:opacity-50"
                              title="Send Email"
                            >
                              <Mail className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDownloadPDF(echallan.id)}
                              disabled={actionLoading[echallan.id]}
                              className="text-purple-600 hover:text-purple-900 p-1 rounded disabled:opacity-50"
                              title="Download PDF"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                            <div className="relative group">
                              <button className="text-gray-600 hover:text-gray-900 p-1 rounded">
                                <MoreVertical className="w-4 h-4" />
                              </button>
                              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="py-1">
                                  <button
                                    onClick={() => handleStatusUpdate(echallan.id, "Paid")}
                                    className="block w-full text-left px-4 py-2 text-sm text-green-600 hover:bg-green-50"
                                  >
                                    Mark as Paid
                                  </button>
                                  <button
                                    onClick={() => handleStatusUpdate(echallan.id, "Disputed")}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                  >
                                    Mark as Disputed
                                  </button>
                                  <button
                                    onClick={() => handleStatusUpdate(echallan.id, "Cancelled")}
                                    className="block w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
                                  >
                                    Mark as Cancelled
                                  </button>
                                  <hr className="my-1" />
                                  <button
                                    onClick={() => handleDeleteEchallan(echallan.id)}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                  >
                                    Delete EChallan
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Create EChallan Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-lg shadow-xl max-w-md w-full"
            >
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Create New EChallan</h3>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Vehicle Number
                    </label>
                    <input
                      type="text"
                      value={newEchallan.vehicle_number}
                      onChange={(e) => setNewEchallan({ ...newEchallan, vehicle_number: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter vehicle number"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Violation Type
                    </label>
                    <select
                      value={newEchallan.violation_type}
                      onChange={(e) => setNewEchallan({ ...newEchallan, violation_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select violation type</option>
                      {violationTypes.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Fine Amount
                    </label>
                    <input
                      type="number"
                      value={newEchallan.fine_amount}
                      onChange={(e) => setNewEchallan({ ...newEchallan, fine_amount: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter fine amount"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notes
                    </label>
                    <textarea
                      value={newEchallan.notes}
                      onChange={(e) => setNewEchallan({ ...newEchallan, notes: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows={3}
                      placeholder="Enter any additional notes"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateEchallan}
                    disabled={actionLoading.create}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {actionLoading.create ? "Creating..." : "Create EChallan"}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* EChallan Details Modal */}
        {showEchallanModal && selectedEchallan && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900">
                    EChallan Details #{selectedEchallan.id}
                  </h3>
                  <button
                    onClick={() => setShowEchallanModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">EChallan Information</h4>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-gray-600">EChallan ID:</span>
                        <p className="font-medium">#{selectedEchallan.id}</p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Vehicle Number:</span>
                        <p className="font-medium">{selectedEchallan.vehicle_number}</p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Violation Type:</span>
                        <p className="font-medium">{selectedEchallan.violation_type}</p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Fine Amount:</span>
                        <p className="font-medium text-green-600">₹{selectedEchallan.fine_amount}</p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Status:</span>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-2 ${statusColors[selectedEchallan.status]}`}
                        >
                          {selectedEchallan.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Issue Date:</span>
                        <p className="font-medium">
                          {new Date(selectedEchallan.date_issued).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Owner Information</h4>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-gray-600">Owner Name:</span>
                        <p className="font-medium">
                          {selectedEchallan.owner?.owner_name || "N/A"}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Email:</span>
                        <p className="font-medium">
                          {selectedEchallan.owner?.email || "N/A"}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Phone:</span>
                        <p className="font-medium">
                          {selectedEchallan.owner?.phone || "N/A"}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Address:</span>
                        <p className="font-medium">
                          {selectedEchallan.owner?.address || "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Evidence Section */}
                {(selectedEchallan.evidence_image || selectedEchallan.evidence_video) && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Evidence</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedEchallan.evidence_image && (
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Evidence Image:</p>
                          <img
                            src={selectedEchallan.evidence_image}
                            alt="Evidence"
                            className="w-full h-32 object-cover rounded-lg border"
                          />
                        </div>
                      )}
                      {selectedEchallan.evidence_video && (
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Evidence Video:</p>
                          <video
                            src={selectedEchallan.evidence_video}
                            controls
                            className="w-full h-32 rounded-lg border"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {selectedEchallan.notes && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Notes</h4>
                    <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                      {selectedEchallan.notes}
                    </p>
                  </div>
                )}

                {selectedEchallan.dispute_reason && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Dispute Information</h4>
                    <p className="text-gray-700 bg-red-50 p-3 rounded-lg">
                      <strong>Reason:</strong> {selectedEchallan.dispute_reason}
                    </p>
                    {selectedEchallan.dispute_date && (
                      <p className="text-sm text-gray-600 mt-2">
                        Disputed on: {new Date(selectedEchallan.dispute_date).toLocaleString()}
                      </p>
                    )}
                  </div>
                )}

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => handleSendEmail(selectedEchallan.id)}
                    disabled={actionLoading[selectedEchallan.id]}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    <Mail className="w-4 h-4" />
                    Send Email
                  </button>
                  <button
                    onClick={() => handleDownloadPDF(selectedEchallan.id)}
                    disabled={actionLoading[selectedEchallan.id]}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
