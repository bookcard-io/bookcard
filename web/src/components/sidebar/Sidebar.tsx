"use client";

import { useState } from "react";
import { useSidebar } from "@/contexts/SidebarContext";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { LibraryOutline } from "@/icons/LibraryOutline";
import { SharpDevicesFold } from "@/icons/SharpDevicesFold";
import styles from "./Sidebar.module.scss";

interface NavSection {
  title: string;
  items: string[];
}

const navSections: NavSection[] = [
  {
    title: "MY LIBRARY",
    items: ["Add books", "Library/options", "Switch/add library"],
  },
  {
    title: "MY SHELVES",
    items: ["To-read", "DNF", "Estonian Sci-Fi", "Recommended", "Add shelf"],
  },
  {
    title: "DEVICES",
    items: ["My Kindle", "iPad Air"],
  },
];

const sectionIcons: Record<
  string,
  React.ComponentType<React.SVGProps<SVGSVGElement>>
> = {
  "MY LIBRARY": LibraryBuilding,
  "MY SHELVES": LibraryOutline,
  DEVICES: SharpDevicesFold,
};

export function Sidebar() {
  const { isCollapsed, setIsCollapsed } = useSidebar();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["MY LIBRARY", "MY SHELVES", "DEVICES"]),
  );

  const toggleSection = (title: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(title)) {
      newExpanded.delete(title);
    } else {
      newExpanded.add(title);
    }
    setExpandedSections(newExpanded);
  };

  const handleLinkClick = () => {
    // No-op for now
  };

  return (
    <aside
      className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ""}`}
    >
      <div className={styles.header}>
        <div className={styles.logoContainer}>
          <img
            src="/logo.svg"
            alt="Fundamental Logo"
            width={24}
            height={24}
            className={styles.logo}
          />
          {!isCollapsed && (
            <span className={styles.brandName}>Fundamental</span>
          )}
        </div>
        <button
          type="button"
          className={styles.menuButton}
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label="Toggle sidebar"
        >
          <i className="pi pi-bars" aria-hidden="true" />
        </button>
      </div>

      <nav className={styles.nav}>
        {navSections.map((section) => {
          const IconComponent = sectionIcons[section.title];
          return (
            <div key={section.title} className={styles.section}>
              <button
                type="button"
                className={styles.sectionHeader}
                onClick={() => toggleSection(section.title)}
              >
                {IconComponent && (
                  <IconComponent
                    className={styles.sectionIcon}
                    aria-hidden="true"
                  />
                )}
                {!isCollapsed && (
                  <span className={styles.sectionTitle}>{section.title}</span>
                )}
                {!isCollapsed && (
                  <i
                    className={`pi ${
                      expandedSections.has(section.title)
                        ? "pi-chevron-up"
                        : "pi-chevron-down"
                    } ${styles.chevron}`}
                    aria-hidden="true"
                  />
                )}
              </button>
              {expandedSections.has(section.title) && !isCollapsed && (
                <ul className={styles.sectionItems}>
                  {section.items.map((item) => (
                    <li key={item}>
                      <button
                        type="button"
                        onClick={handleLinkClick}
                        className={styles.navLink}
                      >
                        {item}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </nav>

      <div className={styles.footer}>
        <button
          type="button"
          onClick={handleLinkClick}
          className={styles.settingsLink}
          aria-label="Fundamental Settings"
        >
          <i className="pi pi-cog"></i>
          {!isCollapsed && <span>Admin Settings</span>}
        </button>
      </div>
    </aside>
  );
}
