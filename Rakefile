# Rakefile for HTIDP Development

desc "Build the Go reference server"
task :build do
  puts "Building Go server..."
  Dir.chdir("server") do
    sh "go build -o htidp-server ."
  end
end

desc "Start the Go reference server"
task :server => :build do
  puts "Starting HTIDP server on port 8000..."
  # Use spawn to run in background
  @server_pid = spawn("PORT=8000 ./server/htidp-server")
end

desc "Start Python server for client files"
task :client_server do
  puts "Starting Python client server on port 8001..."
  @client_pid = spawn("python3 -m http.server 8001", chdir: "client")
end

desc "Open the client in the browser"
task :open do
  puts "Opening HTIDP client..."
  sleep 1 # Give servers a moment to start
  url = "http://localhost:8001/index.html"
  
  if RUBY_PLATFORM =~ /linux/
    sh "xdg-open #{url}"
elsif RUBY_PLATFORM =~ /darwin/
    sh "open #{url}"
  else
    puts "Please open #{url} manually."
  end
end

desc "Start everything"
task :start => [:server, :client_server, :open] do
  puts "HTIDP Development Environment is running."
  puts "Press Ctrl+C to stop all servers."
  
  trap("INT") do
    puts "\nStopping servers..."
    Process.kill("TERM", @server_pid) if @server_pid
    Process.kill("TERM", @client_pid) if @client_pid
    exit
  end

  # Keep the main process alive
  loop { sleep 1 }
end

task :default => :start
