"use client";

import { Globe, Shield } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import RelayManager from "@/components/RelayManager";

export default function Home() {
  return (
    <main className="h-screen flex flex-col items-center justify-center p-2 bg-gradient-to-br from-background via-background to-muted/20 overflow-hidden">
      <div className="w-full max-w-5xl h-full max-h-[90vh] bg-card/95 backdrop-blur-sm shadow-2xl border border-border/50 flex flex-col overflow-hidden relative">
        <header className="relative bg-gradient-to-r from-primary/10 via-primary/5 to-background px-8 py-3 border-b border-border/50 flex-shrink-0">
          <div className="absolute top-2 right-4 z-20">
            <ModeToggle />
          </div>

          <div className="flex items-center justify-start gap-4">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center ring-2 ring-primary/20">
              <Shield className="w-7 h-7 text-primary" />
            </div>
            <div className="text-left">
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                GateController
              </h1>
              {/* <p className="text-muted-foreground text-xs font-medium">
                Advanced Relay Control System
              </p> */}
            </div>
          </div>
        </header>

        <section className="flex-grow min-h-0 p-6 overflow-y-auto">
          <RelayManager />
        </section>

        <footer className="px-8 py-2 bg-muted/30 border-t border-border/50 flex-shrink-0">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              © 2025 Plate Recognizer, a subsidiary of ParkPow, Inc. All rights
              reserved.
            </p>
            <a
              href="https://platerecognizer.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors duration-200 group"
            >
              <Globe className="w-4 h-4 group-hover:rotate-12 transition-transform duration-200" />
              <span className="font-medium">Powered by Platerecognizer</span>
            </a>
          </div>
        </footer>
      </div>

      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-48 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      </div>
    </main>
  );
}
