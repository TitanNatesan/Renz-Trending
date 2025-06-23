"use client";

import { useEffect, useState } from "react";
import Navbar from "./Components/Header/Navbar";
import Hero from "./Components/Hero/Hero";
import axios from "axios";
import { baseurl } from "./utils/Url";
import Categories from "./Components/Categories/Categories";

export default function Home() {

  const [homeData, setHomeData] = useState(null);

  useEffect(() => {
    axios.get(`${baseurl}/home/`)
      .then((res) => {
        setHomeData(res.data);
      })
      .catch((err) => {
        console.error("Error fetching home data:", err);
      });
  }, [])

  return (
    <>
      <Navbar />
      <main className="main">
        <Hero />
        <Categories categories={homeData?.categories || []} />
      </main>

    </>
  );
}
