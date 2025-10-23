FROM node:22.12.0

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Run port for Vite
EXPOSE 5173

# Run development with open host
CMD ["npm", "run", "dev", "--", "--host"]
