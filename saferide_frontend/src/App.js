import { BrowserRouter as Router, Routes, Route, Link, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Detection from "./pages/Detection";
import PreviewDetection from "./pages/PreviewDetection";
import ViolationsTable from "./pages/ViolationsTable";
import LiveDetection from "./pages/LiveDetection";
import SavedViolations from "./pages/SavedViolations";
import Profile from "./pages/Profile";

function App() {
	const isLoggedIn = !!localStorage.getItem("access");

	return (
		<Router>
			<div className="min-h-screen bg-gray-100">
				{/* Navbar */}
				<nav className="bg-blue-600 p-4 text-white flex justify-between items-center shadow-md">
					<div className="flex items-center gap-2">
						{/* Removed logo image */}
						<h1 className="text-xl font-bold">SafeRide</h1>
					</div>
					<div className="space-x-6">
						<Link to="/">Dashboard</Link>
						<Link to="/about">About</Link>
						{!isLoggedIn ? (
							<>
								<Link to="/login">Login</Link>
								<Link to="/signup">Signup</Link>
							</>
						) : (
							<Link to="/profile" className="bg-blue-700 px-3 py-1 rounded hover:bg-blue-800">
								My Profile
							</Link>
						)}
					</div>
				</nav>

				{/* Routes */}
				<Routes>
					<Route path="/" element={isLoggedIn ? <Dashboard /> : <Navigate to="/login" />} />
					<Route path="/about" element={<About />} />
					<Route path="/login" element={<Login />} />
					<Route path="/signup" element={<Signup />} />
					<Route path="/detection" element={<Detection />} />
					<Route path="/preview-detection" element={<PreviewDetection />} />
					<Route path="/violations-table" element={<ViolationsTable />} />
					<Route path="/live-detection" element={<LiveDetection />} />
					<Route path="/saved-violations" element={<SavedViolations />} />
					<Route path="/profile" element={<Profile />} />
				</Routes>
			</div>
		</Router>
	);
}

export default App;
