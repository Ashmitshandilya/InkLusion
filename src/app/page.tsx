import SmoothScroll from "@/components/SmoothScroll";
import InkCanvas from "@/components/InkCanvas";
import Nav from "@/components/Nav";
import Hero from "@/components/Hero";
import Story from "@/components/Story";
import Process from "@/components/Process";
import Work from "@/components/Work";
import IdeaTeaser from "@/components/IdeaTeaser";
import Booking from "@/components/Booking";

export default function Home() {
  return (
    <>
      <SmoothScroll />
      <InkCanvas />
      <Nav />
      <main className="relative z-10">
        <Hero />
        <Story />
        <Process />
        <Work />
        <IdeaTeaser />
        <Booking />
      </main>
    </>
  );
}
