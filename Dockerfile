FROM maven:3.9.6-eclipse-temurin-21-slim AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM amazoncorretto:21-alpine-jre
WORKDIR /app
COPY --from=build /app/target/database-import-0.0.1-SNAPSHOT.jar /app/database-import.jar
ENTRYPOINT ["java", "-jar", "/app/database-import.jar"]


