# Use Node 20 slim as base
FROM node:20-slim

# Install pnpm globally
RUN npm install -g pnpm

# Set work directory
WORKDIR /app

# Copy package.json and lock file (if exists)
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy the rest of the frontend source
COPY . .

# Expose Vite's default dev port
EXPOSE 5173

# Start Vite dev server with host binding
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
