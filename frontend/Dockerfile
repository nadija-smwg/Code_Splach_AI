# ============================================================
# frontend/Dockerfile
# ============================================================
#
# This uses a 2-STAGE BUILD — a very common Docker pattern:
#
#   Stage 1 (builder): Install Node.js deps + build the React app
#                      → produces a /dist folder of static files
#
#   Stage 2 (runner):  Use a tiny nginx server to serve /dist
#                      → the final image has NO Node.js in it!
#
# WHY 2 STAGES?
# If you just used one stage, you'd have Node.js + node_modules
# (hundreds of MB) inside the final image just to serve static HTML.
# With 2 stages, the final image is ~30MB instead of ~700MB.
# ============================================================

# ── STAGE 1: Build ──────────────────────────────────────────
# "AS builder" gives this stage a name so Stage 2 can reference it.
FROM node:20-alpine AS builder

# Set working directory inside the builder container
WORKDIR /app

# Copy package files first (for caching — same trick as backend)
COPY package.json package-lock.json ./

# Install all Node dependencies (including devDependencies for build)
RUN npm ci

# Copy all frontend source code into the container
COPY . .

# Accept build-time argument from docker-compose.yml
# ARG = available only during the BUILD phase
ARG VITE_API_URL=http://localhost:8000/api
# ENV = makes it visible to the build process (Vite reads VITE_* env vars)
ENV VITE_API_URL=$VITE_API_URL

# Run the production build — outputs to /app/dist
# This runs: tsc -b && vite build (from package.json "build" script)
RUN npm run build


# ── STAGE 2: Serve ──────────────────────────────────────────
# Start fresh from a tiny nginx image — NO Node.js here at all!
FROM nginx:alpine

# Copy only the compiled /dist output from the builder stage
# "COPY --from=builder" = grab files from Stage 1's filesystem
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config (handles React Router's client-side routes)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (nginx default HTTP port)
EXPOSE 80

# nginx:alpine already has a default CMD to start nginx, so we don't
# need to specify CMD here — it's inherited from the base image.
