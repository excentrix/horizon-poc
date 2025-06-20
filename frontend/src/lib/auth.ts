// frontend/src/lib/auth.ts
import NextAuth from "next-auth";
import { JWT } from "next-auth/jwt";
import GithubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";
import Nodemailer from "next-auth/providers/nodemailer";
import NeonAdapter from "@auth/neon-adapter";
import { Pool } from "@neondatabase/serverless";

export const { auth, handlers, signIn, signOut } = NextAuth(() => {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  return {
    providers: [
      GithubProvider({
        clientId: process.env.GITHUB_ID!,
        clientSecret: process.env.GITHUB_SECRET!,
      }),
      GoogleProvider({
        clientId: process.env.GOOGLE_ID!,
        clientSecret: process.env.GOOGLE_SECRET!,
      }),
      Nodemailer({
        server: process.env.EMAIL_SERVER,
        from: process.env.EMAIL_FROM,
      }),
    ],
    adapter: NeonAdapter(pool),

    callbacks: {
      async jwt({ token, user, account }): Promise<JWT> {
        if (user) {
          token.id = user.id;
          token.email = user.email;
          token.name = user.name;
          token.picture = user.image;
        }
        return token;
      },

      async session({ session, token, user }) {
        if (token && session.user) {
          session.user.id = token.id as string;
          session.user.email = token.email as string;
          session.user.name = token.name as string;
          session.user.image = token.picture as string;
        }
        // If using database sessions, use user object instead
        if (user && session.user) {
          session.user.id = user.id;
        }
        return session;
      },

      async signIn({ user, account, profile }) {
        // Always allow sign in
        return true;
      },
    },

    session: {
      strategy: "database",
      maxAge: 30 * 24 * 60 * 60, // 30 days
      updateAge: 24 * 60 * 60, // 24 hours
    },

    jwt: {
      maxAge: 30 * 24 * 60 * 60, // 30 days
    },

    pages: {
      signIn: "/auth/signin",
      error: "/auth/error",
    },

    debug: process.env.NODE_ENV === "development",
  };
});
