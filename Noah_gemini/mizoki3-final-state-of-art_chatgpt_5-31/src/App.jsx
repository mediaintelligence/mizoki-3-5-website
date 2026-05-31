import { Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { HomePage } from "./pages/HomePage";
import { PlatformPage } from "./pages/PlatformPage";
import { SimulatorPage } from "./pages/SimulatorPage";
import { EnginePage } from "./pages/EnginePage";
import { ControlPlanePage } from "./pages/ControlPlanePage";
import { DivisionsPage } from "./pages/DivisionsPage";
import { GovernancePage } from "./pages/GovernancePage";
import { KpisPage } from "./pages/KpisPage";
import { BlogPage } from "./pages/BlogPage";
import { ReviewPage } from "./pages/ReviewPage";
import { StoryPage } from "./pages/StoryPage";
import { ContactPage } from "./pages/ContactPage";
import { NotFound } from "./pages/NotFound";

export default function App() {
  return (
    <div className="min-h-screen bg-[#020203] text-slate-100 antialiased">
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/platform" element={<PlatformPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/engine" element={<EnginePage />} />
          <Route path="/control-plane" element={<ControlPlanePage />} />
          <Route path="/divisions" element={<DivisionsPage />} />
          <Route path="/governance" element={<GovernancePage />} />
          <Route path="/kpis" element={<KpisPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/story" element={<StoryPage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
