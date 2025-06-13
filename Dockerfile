FROM swift:latest
WORKDIR /app
COPY . .
RUN swift build
CMD ["swift", "run", "DockGlo"]