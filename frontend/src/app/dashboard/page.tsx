// app/page.tsx
"use client";

import { useMediaQuery } from "@/hooks/use-media-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ListCheckIcon } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import ConcentricCirclesButton from "@/components/ccbutton";
import AppleStyleContainer from "@/components/apple-style-container";
import { FloatingDock } from "@/components/ui/floating-dock";
import {
  IconBrandGithub,
  IconBrandX,
  IconExchange,
  IconHome,
  IconNewSection,
  IconTerminal2,
} from "@tabler/icons-react";
import { useState } from "react";
import AnimatedList from "@/components/ui/bits/comps/AnimatedList/AnimatedList";

export default function Dashboard() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [date, setDate] = useState<Date | undefined>(new Date());

  return (
    <>
      {/* Web Layout - Hidden on mobile */}
      <div className="hidden md:block ">
        <div className="border border-gray-700 rounded-lg p-4 grid grid-cols-4 gap-4 h-screen">
          {/* Left Column */}
          <div className="col-span-1 flex flex-col gap-4">
            <div className="h-1/2 group/bento shadow-input row-span-1 flex flex-col justify-between space-y-2 rounded-xl border-2 border-lemon/30 bg-dark p-4 transition duration-200 hover:shadow-xl hover:shadow-lemon/10 dark:border-white/[0.2] dark:bg-black dark:shadow-none">
              <div className="flex items-center gap-2">
                <ListCheckIcon />
                Goals
              </div>
              <div className="flex items-center justify-start">
                <AnimatedList
                  items={items}
                  onItemSelect={(item, index) => console.log(item, index)}
                  showGradients={false}
                  itemClassName="p-0 rounded-lg bg-lemon/10 hover:bg-lemon/20 transition-colors"
                  enableArrowNavigation={true}
                  displayScrollbar={false}
                  className="w-full"
                />
              </div>
            </div>
            <div className="h-1/2 group/bento shadow-input row-span-1 flex flex-col space-y-4 rounded-xl border-2 border-lemon/30 bg-dark p-4 transition duration-200 hover:shadow-xl dark:border-white/[0.2] dark:bg-black dark:shadow-none">
              <div className="flex items-center gap-2">
                <ListCheckIcon />
                Calendar
              </div>
              <div className="px-2 w-full h-10/12">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  className="w-full h-full bg-dark p-0"
                  animate
                />
              </div>
            </div>
          </div>

          {/* Middle Column */}
          <div className="col-span-2 flex flex-col gap-4">
            <Card className="border-2 border-lemon/30 h-16 bg-dark">
              <CardContent className="flex items-center justify-center h-full">
                <span className="text-gray-300">user info</span>
              </CardContent>
            </Card>
            {/* <Card className="border border-gray-700 flex-1">
              <CardContent className="flex items-center justify-center h-full">
                <span className="text-gray-300">start session</span>
              </CardContent>
            </Card> */}
            {/* <div className="flex-1 group/bento shadow-input row-span-1 flex flex-col space-y-4 rounded-xl border border-lemon/30 bg-lemon p-4 transition duration-200 hover:shadow-xl dark:border-white/[0.2] dark:bg-black dark:shadow-none">
              <div className="p-2 w-full h-full items-center justify-center flex"> */}
            {/* <Button className="h-40 w-40 rounded-full bg-dark/20 hover:scale-110">
                  start
                </Button> */}
            <AppleStyleContainer
              // backgroundColor="#ffea96"
              buttonProps={{
                text: "start",
                colorScheme: "lemon",
                size: "lg",
                onClick: () => alert("Button clicked!"),
              }}
            />
            {/* </div>
            </div> */}
            <FloatingDock
              mobileClassName="translate-y-20" // only for demo, remove for production
              items={links}
              desktopClassName="bg-lemon/10 w-full items-center justify-center p-4 rounded-t-lg shadow-lg"
            />
          </div>

          {/* Right Column */}
          <div className="col-span-1 flex flex-col gap-4">
            <div className="h-1/2 group/bento shadow-input row-span-1 flex flex-col justify-between space-y-4 rounded-xl border-2 border-lemon/30 bg-dark p-4 transition duration-200 hover:shadow-xl dark:border-white/[0.2] dark:bg-black dark:shadow-none">
              <div className="flex items-center gap-2">
                <ListCheckIcon />
                Mentors
              </div>
              <div className="">
                {/* <div className=" mb-2 font-sans font-bold text-neutral-600 dark:text-lemon/30">
                  Mentors
                </div>
                <div className="font-sans text-xs font-normal text-neutral-600 dark:text-neutral-300">
                  All mentors go here
                </div> */}
                <AnimatedList
                  items={items}
                  onItemSelect={(item, index) => console.log(item, index)}
                  showGradients={false}
                  itemClassName="p-0 rounded-lg bg-lemon/10 hover:bg-lemon/20 transition-colors"
                  enableArrowNavigation={true}
                  displayScrollbar={false}
                  className="w-full h-1/2"
                />
              </div>
            </div>
            <div className="h-1/2 group/bento shadow-input row-span-1 flex flex-col justify-between space-y-4 rounded-xl border-2 border-lemon/30 bg-dark p-4 transition duration-200 hover:shadow-xl dark:border-white/[0.2] dark:bg-black dark:shadow-none">
              <div className="flex items-center gap-2">
                <ListCheckIcon />
                Sessions
              </div>
              <div className="">
                {/* <div className=" mb-2 font-sans font-bold text-neutral-600 dark:text-lemon/30">
                  Sessions
                </div>
                <div className="font-sans text-xs font-normal text-neutral-600 dark:text-neutral-300">
                  All sessions go here
                </div> */}
                <AnimatedList
                  items={items}
                  onItemSelect={(item, index) => console.log(item, index)}
                  showGradients={false}
                  itemClassName="p-0 rounded-lg bg-lemon/10 hover:bg-lemon/20 transition-colors"
                  enableArrowNavigation={true}
                  displayScrollbar={false}
                  className="w-full h-1/2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Layout - Visible only on mobile */}
      <div className="md:hidden">
        <div className="border border-gray-700 rounded-lg p-4 flex flex-col gap-4">
          <Card className="border border-gray-700 h-16">
            <CardContent className="flex items-center justify-center h-full">
              <span className="text-gray-300">horizon</span>
            </CardContent>
          </Card>
          <Card className="border border-gray-700 h-40">
            <CardContent className="flex items-center justify-center h-full">
              <span className="text-gray-300">sessions</span>
            </CardContent>
          </Card>
          <Card className="border border-gray-700 h-40">
            <CardContent className="flex items-center justify-center h-full">
              <span className="text-gray-300">start session</span>
            </CardContent>
          </Card>
          <Card className="border border-gray-700 h-16">
            <CardContent className="flex items-center justify-center h-full">
              <span className="text-gray-300">dock</span>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

const GridItem = () => (
  <div className="group/bento shadow-input row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-lemon/30 bg-dark p-4 transition duration-200 hover:shadow-xl dark:border-white/[0.2] dark:bg-black dark:shadow-none">
    <div className="flex items-center gap-2">
      <ListCheckIcon />
      Goals
    </div>
    <div className="transition duration-200 group-hover/bento:translate-x-2">
      <div className=" mb-2 font-sans font-bold text-neutral-600 dark:text-lemon/30">
        Goals
      </div>
      <div className="font-sans text-xs font-normal text-neutral-600 dark:text-neutral-300">
        All goals go here
      </div>
    </div>
  </div>
);
const items = [
  "Item 1",
  "Item 2",
  "Item 3",
  "Item 4",
  "Item 5",
  "Item 6",
  "Item 7",
  "Item 8",
  "Item 9",
  "Item 10",
];

const links = [
  {
    title: "Home",
    icon: (
      <IconHome className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },

  {
    title: "Products",
    icon: (
      <IconTerminal2 className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },
  {
    title: "Components",
    icon: (
      <IconNewSection className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },
  {
    title: "Aceternity UI",
    icon: (
      <img
        src="https://assets.aceternity.com/logo-dark.png"
        width={20}
        height={20}
        alt="Aceternity Logo"
      />
    ),
    href: "#",
  },
  {
    title: "Changelog",
    icon: (
      <IconExchange className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },

  {
    title: "Twitter",
    icon: (
      <IconBrandX className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },
  {
    title: "GitHub",
    icon: (
      <IconBrandGithub className="h-full w-full text-neutral-500 dark:text-neutral-300" />
    ),
    href: "#",
  },
];
